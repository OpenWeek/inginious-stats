import os
import web
from urllib.parse import parse_qs
import numpy as np
from scipy import stats  # NOTE sometimes triggers a warning
from dateutil.parser import parse as date_parse

from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage
from inginious.common.tags import Tag
from datetime import datetime, date, timedelta

PATH_TO_PLUGIN = os.path.abspath(os.path.dirname(__file__))


def add_admin_menu(course): # pylint: disable=unused-argument
    """ Add a menu for the contest settings in the administration """
    return ('adv_stats', '<i class="fa fa-bar-chart fa-fw"></i>&nbsp; Advanced statistics')


def parse_query(query):
    """
    Parses the query for a chart and returns the relevant parameters
    that should be used to make the query on the database.
    @return: a tuple with all the relevant query information
    """
    # Date range
    if query.stats_to is not None and query.stats_to != "":
        start_time = date_parse(query.stats_to)
    else:
        start_time = datetime.min

    if query.stats_from is not None and query.stats_from != "":
        end_time = date_parse(query.stats_from)
    else:
        end_time = datetime.now().replace(minute=0, second=0, microsecond=0)

    date_range = [start_time, end_time]

    # Exercises filter
    exercise_list = [name.strip()
                     for name in query.filter_exercises.split(",")
                     if name.strip() != ""]
    # Tags filter
    tag_list = [tag.strip()
                for tag in query.filter_tags.split(",")
                if tag.strip() != ""]

    # Min-max grades
    min_grade = 0
    if query.min_submission_grade is not None and query.min_submission_grade != "":
        percentage = query.min_submission_grade
        if percentage.endswith('%'):
            percentage = percentage[:-1]
        min_grade = float(percentage)
    max_grade = 100
    if query.max_submission_grade is not None and query.max_submission_grade != "":
        percentage = query.max_submission_grade
        if percentage.endswith('%'):
            percentage = percentage[:-1]
        max_grade = float(percentage)
    grade_bounds = (min_grade, max_grade)

    return (query.chart_type, date_range, exercise_list, tag_list, grade_bounds, query.submissions_filter)

def apply_grade_filter(grade_list, grade_bounds):
    """
    Returns the list `grade_list` without all the grades that are not
    in the bounds `grade_bounds`.
    """
    (minimum, maximum) = grade_bounds
    return [grade
            for grade in grade_list
            if grade >= minimum and grade <= maximum]


def aggregate_all_grades(query_result):
    """
    Given a list of dicts where each dict represents an exercise and
    contains a list of all the grades for this exercise,
    aggregates the grades for all the exercises in just one list
    and returns it.
    """
    answer = []
    for exercise in query_result:
        if "allGrades" in exercise:
            answer.extend(exercise["allGrades"])
    return answer


def compute_advanced_stats(data):
    """
    Given a list of (numeric) data points `data`,
    computes advanced statistics on them.
    Returns a dict containing each stat.
    The stats computed are:
        - count
        - min
        - max
        - mean
        - median
        - mode
        - variance
        - standard deviation (key "std_deviation")
    """
    count = len(data)
    if count == 0:
        return None

    minimum = np.amin(data)
    maximum = np.amax(data)
    mean = np.mean(data)
    median = np.median(data)
    mode = stats.mode(data).mode[0]
    variance = np.var(data)
    std_deviation = np.sqrt(variance)

    return {
        "count": count,
        "min": minimum,
        "max": maximum,
        "mean": mean,
        "median": median,
        "mode": mode,
        "variance": variance,
        "std_deviation": std_deviation
    }


class AdvancedCourseStatisticClass(INGIniousAdminPage):

    def _tasks_stats(self, courseid, tasks, daterange):
        """
        Get statistics about the task submissions of a courseid
        :param: - courseid: id of an inginious course
                - list of the tasks for courseid
                - daterange period for the query
        :return: list of dict containing the data per task per user
        """
        stats_tasks = self.database.submissions.aggregate(
            [{"$match": {"submitted_on": {"$gte": daterange[0], "$lt": daterange[1]}, "courseid": courseid}},
             {"$unwind":"$username"},
             {"$group": {"_id": "$taskid", "averageGrade": {"$avg": "$grade"},
                         "minGrade": {"$min": "$grade"},"maxGrade": {"$max": "$grade"},
                         "allGrades": {"$push": "$grade"}, "username": {"$first": "$username"},
                         "submissions": {"$sum": 1}, "validSubmissions":
                 {"$sum": {"$cond": {"if": {"$eq": ["$result", "success"]}, "then": 1, "else": 0}}},
                         "tags": {"$first": "$tests"}}
              }])

        return [
            {"_id": x["_id"],
             "name": tasks[x["_id"]].get_name(self.user_manager.session_language()) if x["_id"] in tasks else x["_id"],
             "submissions": x["submissions"],
             "averageGrade": x["averageGrade"],
             "minGrade": x["minGrade"],
             "username": x["username"],
             "maxGrade": x["maxGrade"],
             "allGrades": x["allGrades"],
             #"tags": [y[0].get_name() if len(y) == 1 else "" for y in tasks[x["_id"]].get_tags()],
             "tags": [y for y in x["tags"]],
             "validSubmissions": x["validSubmissions"]}
            for x in stats_tasks
        ]

    def _get_best_submissions(self, courseid, tasks, daterange):
        """
            Gives a list of only the best submission for each studentourseid
            :param: - courseid: id of an inginious course
                - list of the tasks for courseid
                - daterange period for the query
            :return: list of dict containing all best submissions per user
        """
        all_submissions = self.database.submissions.aggregate(
            [{"$match": {"submitted_on": {"$gte": daterange[0], "$lt": daterange[1]}, "courseid": courseid}},
             {"$unwind":"$username"},
             {"$group": {"_id": "$_id", "grade": {"$first": "$grade"}, "task": {"$first": "$taskid"},
                         "username": {"$first": "$username"}, "tags": {"$first": "$tests"}}
              }])
        temp_dict = {}
        for sub in all_submissions:
            if sub["username"]+str(sub["task"]) in temp_dict:
                if sub["grade"] > temp_dict[sub["username"]+str(sub["task"])]["grade"]:
                    temp_dict[sub["username"]+str(sub["task"])] = sub
            else:
                temp_dict[sub["username"]+str(sub["task"])] = sub
        return list(temp_dict.values())

    def _get_task_failed_attempts(self, courseid, taskid, daterange):
        """
            Gives the number of failed attempts before first success
            for each student for the task {taskid} during the range {daterange}
        """
        task_data =  self.database.submissions.aggregate(
            [{"$match": {"submitted_on": {"$gte": daterange[0], "$lt": daterange[1]}, 
              "courseid": courseid, "taskid": {"$in":taskid}}},
            {"$sort": {"submitted_on": 1}}
            ])

        result = {}
        for x in task_data:
            if x["username"][0] not in result:
                if x["result"] == "success":
                    result[x["username"][0]] = {"tries":1, "done":True}
                else:
                    result[x["username"][0]] = {"tries":1, "done":False}
            else:
                if not result[x["username"][0]]["done"]:
                    if x["result"] == "success":
                        result[x["username"][0]]["done"] = True
                    else:
                        result[x["username"][0]]["tries"] +=1
        return result

    def _tags_stats(self, courseid, tasks, daterange):
        """
        Get aggregated statistics about the submissions grouped by tags
        :param: - courseid: id of an inginious course
                - list of the tasks for courseid
                - daterange period for the query
        :return: list of dict containing the data per tag
        """
        stats_tasks = self._tasks_stats(courseid, tasks, daterange)
        tag_stats = {}
        for x in stats_tasks:
            for tag in x["tags"]:
                if tag not in tag_stats and tag != "":
                    tag_stats[tag] = {"submissions": x["submissions"],
                                      "validSubmissions": x["validSubmissions"],
                                      "allGrades": x["allGrades"],
                                      "minGrade": x["minGrade"],
                                      "maxGrade": x["maxGrade"],
                                      "averageGrade": x["averageGrade"]
                                      }
                elif tag != "":
                    tag_stats[tag]["submissions"] += x["submissions"]
                    tag_stats[tag]["validSubmissions"] += x["validSubmissions"]
                    tag_stats[tag]["averageGrade"] = (tag_stats[tag]["averageGrade"]*len(tag_stats[tag]["allGrades"])
                                                      + x["averageGrade"]*len(x["allGrades"])) / (len(tag_stats[tag]["allGrades"])+len(x["allGrades"]))
                    tag_stats[tag]["allGrades"] = [item for sublist in tag_stats[tag]["allGrades"] for item in  x["allGrades"]]
                    tag_stats[tag]["minGrade"] = min(tag_stats[tag]["allGrades"])
                    tag_stats[tag]["maxGrade"] = max(tag_stats[tag]["allGrades"])
        return tag_stats


    def _users_stats(self, courseid, daterange):
        """
        Get statistics about all submissions of an user
        :param: - courseid: id of an inginious course
                - daterange period for the query
        :return: list of dict containing the data per user
        """
        #TODO : not used ?
        stats_users = self.database.submissions.aggregate([
            {"$match": {"submitted_on": {"$gte": daterange[0], "$lt": daterange[1]}, "courseid": courseid}},
            {"$project": {"username": "$username", "result": "$result"}},
            {"$unwind": "$username"},
            {"$group": {"_id": "$username", "submissions": {"$sum": 1}, "validSubmissions":
                {"$sum": {"$cond": {"if": {"$eq": ["$result", "success"]}, "then": 1, "else": 0}}}}
             },
            {"$sort": {"submissions": -1}}])

        return [
            {"name": x["_id"],
             "submissions": x["submissions"],
             "validSubmissions": x["validSubmissions"]}
            for x in stats_users
        ]

    def _graph_stats(self, courseid, daterange):
        # TODO improve
        project = {
            "year": {"$year": "$submitted_on"},
            "month": {"$month": "$submitted_on"},
            "day": {"$dayOfMonth": "$submitted_on"},
            "result": "$result"
        }
        groupby = {"year": "$year", "month": "$month", "day": "$day"}

        method = "day"
        if (daterange[1] - daterange[0]).days < 7:
            project["hour"] = {"$hour": "$submitted_on"}
            groupby["hour"] = "$hour"
            method = "hour"

        min_date = daterange[0].replace(minute=0, second=0, microsecond=0)
        max_date = daterange[1].replace(minute=0, second=0, microsecond=0)
        delta1 = timedelta(hours=1)
        if method == "day":
            min_date = min_date.replace(hour=0)
            max_date = max_date.replace(hour=0)
            delta1 = timedelta(days=1)

        stats_graph = self.database.submissions.aggregate(
            [{"$match": {"submitted_on": {"$gte": min_date, "$lt": max_date+delta1}, "courseid": courseid}},
             {"$project": project},
             {"$group": {"_id": groupby, "submissions": {"$sum": 1}, "validSubmissions":
                 {"$sum": {"$cond": {"if": {"$eq": ["$result", "success"]}, "then": 1, "else": 0}}}}
              },
             {"$sort": {"_id": 1}}])

        increment = timedelta(days=(1 if method == "day" else 0), hours=(0 if method == "day" else 1))

        all_submissions = {}
        valid_submissions = {}

        cur = min_date
        while cur <= max_date:
            all_submissions[cur] = 0
            valid_submissions[cur] = 0
            cur += increment

        for entry in stats_graph:
            c = datetime(entry["_id"]["year"], entry["_id"]["month"], entry["_id"]["day"], 0 if method == "day" else entry["_id"]["hour"])
            all_submissions[c] += entry["submissions"]
            valid_submissions[c] += entry["validSubmissions"]

        all_submissions = sorted(all_submissions.items())
        valid_submissions = sorted(valid_submissions.items())
        return (all_submissions, valid_submissions)

    def _get_all_distribution(self, courseid, tasks, daterange, exec_list, tag_list):
        """
        Get aggregated statistics about all submissions of tags {tag_list} and exercices {exec_list}
        :param: - courseid: id of an inginious course
                - list of the tasks for courseid
                - daterange period for the query
                - exec_list : the list of exercice names
                - tag_list : the list of tags
        :return: single dict containing the data
        """
        stats_tags = self._tags_stats(courseid, tasks, daterange)
        print("="*20 + "TAGS STATS" + "="*20)
        print(stats_tags)
        all_result = []
        
        for tag in tag_list:
            all_result.append(stats_tags[tag]) #Get the stats about wanted tags
            
        stats_exec = self._tasks_stats(courseid, tasks, daterange) #Get other exercices
        print("="*20 + "EXERCISES STATS" + "="*20)
        print(stats_exec)
        for task in stats_exec: #Add any missing exercices
            add = False
            for tag in tag_list:
                if tag in task["tags"]:
                    add = True
            print("asked: '" + str(exec_list) + "' name: '" + str(task["name"].strip()) + "'")
            if (len(exec_list) == 0 or task["name"].strip() in exec_list) and add:
                all_result.append(task)

        if len(all_result) == 0:
            return None

        #Aggregate stats
        # for elem in all_result[1:]:
        #     all_result[0]["submissions"] += elem["submissions"]
        #     all_result[0]["validSubmissions"] += elem["validSubmissions"]
        #     all_result[0]["averageGrade"] = (all_result[0]["averageGrade"] * len(all_result[0]["allGrades"])
        #                                     + elem["averageGrade"]*len(elem["allGrades"])) / (len(all_result[0]["allGrades"]) + len(elem["allGrades"]))
        #     all_result[0]["allGrades"] = [item for sublist in all_result[0]["allGrades"] for item in  elem["allGrades"]]
        #     all_result[0]["minGrade"] = min(all_result[0]["allGrades"])
        #     all_result[0]["maxGrade"] = max(all_result[0]["allGrades"])
        # return all_result[0]  # TODO check correctness
        return aggregate_all_grades(all_result)

    def _get_best_distribution(self, courseid, tasks, daterange, exec_list, tag_list):
        #TODO doc
        best = self._get_best_submissions(courseid, tasks, daterange)
        result = []
        print(best)
        for submission in best:
            result.append(submission["grade"])
        return result

    def _get_before_perfect(self, courseid, tasks, daterange, exec_list):
        #TODO doc
        all_tasks_id = []
        for t in tasks:
            if t in exec_list:
                all_tasks_id.append(tasks[t].get_id())
        print(all_tasks_id)
        data = self._get_task_failed_attempts(courseid, all_tasks_id, daterange)
        return data

    def GET_AUTH(self, courseid, f=None, t=None):
        """ GET Request """
        # TODO no idea what f and t are
        course, __ = self.get_course_and_check_rights(courseid)
        tasks = course.get_tasks()
        now = datetime.now().replace(minute=0, second=0, microsecond=0)

        error = None
        if f == None and t == None:
            daterange = [now - timedelta(days=14), now]
        else:
            try:
                daterange = [datetime.strptime(x[0:16], "%Y-%m-%dT%H:%M") for x in (f, t)]
            except:
                error = "Invalid dates"
                daterange = [now - timedelta(days=14), now]

        return self.template_helper.get_custom_renderer(os.path.join(PATH_TO_PLUGIN, 'templates')).adv_stats(course, None, None)

    def POST_AUTH(self, courseid):
        """POST Request"""
        print("=============>> POST was called")
        course, __ = self.get_course_and_check_rights(courseid)
        tasks = course.get_tasks()

        chart_query = web.input(stats_from='', stats_to='', chart_type='', submissions_filter='', max_submission_grade='', min_submission_grade='', filter_tags='', filter_exercises='')

        (chart_type, daterange, exercises, tags, grade_bounds, all_or_best_submissions) = parse_query(chart_query)
        print("QUERY: " + str((chart_type, daterange, exercises, tags, grade_bounds, all_or_best_submissions)))
        (minimum, maximum) = grade_bounds
        chart_query.min_submission_grade = minimum
        chart_query.max_submission_grade = maximum

        error = None
        data = None
        statistics = None

        if chart_type == "grades-distribution":
            if all_or_best_submissions == "all":
                data = self._get_all_distribution(courseid, tasks, daterange, exercises, tags)
            else:  # "best
                data = self._get_best_distribution(courseid, tasks, daterange, exercises, tags)
            print("DB RETURNED")
            print(data)

            if data is not None:
                # all_grades = aggregate_all_grades(data)
                all_grades = apply_grade_filter(data, grade_bounds)
                print("FILTERED "*3)
                print(all_grades)
                statistics = compute_advanced_stats(all_grades)
                if statistics is not None:
                    statistics["all_grades"] = all_grades

        elif chart_type == "submission-before-perfect":
            data = self._get_before_perfect(courseid, tasks, daterange, exercises)
            print(data)
            if data is not None:
                    statistics = None
        course, __ = self.get_course_and_check_rights(courseid)
        return self.template_helper.get_custom_renderer(os.path.join(PATH_TO_PLUGIN, 'templates')).adv_stats(course, chart_query, statistics)


def init(plugin_manager, course_factory, client, plugin_config):  # pylint: disable=unused-argument
    """ Init the plugin """
    plugin_manager.add_page('/admin/([^/]+)/adv_stats', AdvancedCourseStatisticClass)
    plugin_manager.add_hook('course_admin_menu', add_admin_menu)
    plugin_manager.add_page('/plugins/stats/static/(.+)', StaticMockPage)
    plugin_manager.add_hook('css', lambda: '/plugins/stats/static/adv_stats.css')
    plugin_manager.add_hook('javascript_header', lambda: '/plugins/stats/static/adv_stats.js')


class StaticMockPage(object):
    # TODO: Replace by shared static middleware and let webserver serve the files

    def GET(self, path):
        if not os.path.abspath(PATH_TO_PLUGIN) in os.path.abspath(os.path.join(PATH_TO_PLUGIN, path)):
            raise web.notfound()

        try:
            with open(os.path.join(PATH_TO_PLUGIN, "static", path), 'rb') as file:
                return file.read()
        except:
            raise web.notfound()

    def POST(self, path):
        return self.GET(path)

