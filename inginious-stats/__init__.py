"""
Plugin for INGInious released under AGPL-3.0
Created by a team at OpenWeek2019
Florian Damhaut, Céline Deknop, Simon Gustin and Maxime Mawait
"""

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
    start_time = datetime.min
    if query.stats_to is not None and query.stats_to != "":
        start_time = date_parse(query.stats_to)

    end_time = datetime.now().replace(minute=0, second=0, microsecond=0)
    if query.stats_from is not None and query.stats_from != "":
        end_time = date_parse(query.stats_from)

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
    result = []
    for exercise in query_result:
        if "allGrades" in exercise:
            result.extend(exercise["allGrades"])
    return result
def process_nb_attempts_dict(query_result):
    """
    Given a dict containing the number of attempts before 100% for each user
    and task,
    returns a list of all the number of attempts (without the additional
    information contained in the dict).
    """
    result = []
    for username in query_result:
        for task_id in query_result[username]:
            result.append(query_result[username][task_id]["attempts"])
    return result


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

    return {
        "count": count,
        "min": np.amin(data),
        "max": np.amax(data),
        "mean": np.mean(data),
        "median": np.median(data),
        "mode": stats.mode(data).mode[0],
        "variance": np.var(data),
        "std_deviation": np.std(data)
    }
def compute_temporal_advanced_stats(data):
    """
    Given a list of temporal data points `data`,
    computes the count, min and max.
    Returns a dict with the same keys as the one returned by
    `compute_advanced_stats`.
    """
    count = len(data)
    if count == 0:
        return None

    return {
        "count": count,
        "min": np.amin(data),
        "max": np.amax(data),
        "mean": -1,
        "median": -1,
        "mode": -1,
        "variance": -1,
        "std_deviation": -1
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
             }]
        )

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

    def _get_best_submissions(self, courseid, tasks, tasks_id, daterange):
        """
            Gives a list of only the best submission for each studentourseid
            :param: - courseid: id of an inginious course
                - list of the tasks for courseid
                - daterange period for the query
            :return: list of dict containing all best submissions per user
        """
        all_submissions = self.database.submissions.aggregate(
            [{"$match": {"submitted_on": {"$gte": daterange[0], "$lt": daterange[1]}, "courseid": courseid,
              "taskid": {"$in":tasks_id}}},
             {"$unwind":"$username"},
             {"$group": {"_id": "$_id", "grade": {"$first": "$grade"}, "task": {"$first": "$taskid"},
                         "username": {"$first": "$username"}, "tags": {"$first": "$tests"}}
             }]
        )

        temp_dict = {}
        for sub in all_submissions:
            if sub["username"]+str(sub["task"]) in temp_dict:
                if sub["grade"] > temp_dict[sub["username"]+str(sub["task"])]["grade"]:
                    temp_dict[sub["username"]+str(sub["task"])] = sub
            else:
                temp_dict[sub["username"]+str(sub["task"])] = sub
        return list(temp_dict.values())

    def _get_task_failed_attempts(self, courseid, taskid, daterange, grade_bounds):
        """
            Gives the number of failed attempts before first success
            for each student for the task {taskid} during the range {daterange}
            and taking into account only attempts with grade in {grade_bounds}.
        """
        (minimum, maximum) = grade_bounds

        if len(taskid) == 0:
            task_data =  self.database.submissions.aggregate(
                [{"$match": {"submitted_on": {"$gte": daterange[0], "$lt": daterange[1]},
                  "courseid": courseid}},
                 {"$sort": {"submitted_on": 1}}]
            )
        else:
            task_data =  self.database.submissions.aggregate(
                [{"$match": {"submitted_on": {"$gte": daterange[0], "$lt": daterange[1]},
                  "courseid": courseid, "taskid": {"$in":taskid}}},
                 {"$sort": {"submitted_on": 1}}]
            )

        result = {}
        for x in task_data:
            username = x["username"][0]
            task_id = x["taskid"]
            if username not in result:
                result[username] = dict()
            if task_id not in result[username]:
                result[username][task_id] = {"attempts": 0, "done": False}

            if x["result"] == "success":
                result[username][task_id]["done"] = True

            if x["grade"] < minimum or x["grade"] > maximum:
                continue
            print("done? " + str(result[username][task_id]["done"]))
            if not result[username][task_id]["done"]:
                result[username][task_id]["attempts"] += 1
        return result

    def _get_submissions_by_time(self, courseid, taskid, daterange, grade_bounds):
        """
            Gives the number of failed attempts before first success
            for each student for the task {taskid} during the range {daterange}
            and taking into account only attempts with grade in {grade_bounds}.
        """
        (minimum, maximum) = grade_bounds

        if len(taskid) == 0:
            task_data =  self.database.submissions.aggregate(
                [{"$match": {"submitted_on": {"$gte": daterange[0], "$lt": daterange[1]},
                  "courseid": courseid}},
                 {"$sort": {"submitted_on": 1}}]
            )
        else:
            task_data =  self.database.submissions.aggregate(
                [{"$match": {"submitted_on": {"$gte": daterange[0], "$lt": daterange[1]},
                  "courseid": courseid, "taskid": {"$in":taskid}}},
                 {"$sort": {"submitted_on": 1}}]
            )

        timestamps = []
        submissions_per_timestamp = []
        for x in task_data:
            current_date = x["submitted_on"].date().isoformat()
            if timestamps and current_date == timestamps[-1] :
                submissions_per_timestamp[-1] += 1
            else :
                timestamps.append(current_date)
                submissions_per_timestamp += [1]

        return (timestamps, submissions_per_timestamp)

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
            if (len(tag_list) == 0):
                add = True
            for tag in tag_list:
                if tag in task["tags"]:
                    add = True
            if (len(exec_list) == 0 or task["name"].strip() in exec_list) and add:
                all_result.append(task)

        if len(all_result) == 0:
            return None

        return aggregate_all_grades(all_result)

    def _get_best_distribution(self, courseid, tasks, daterange, exec_list, tag_list):
        #TODO doc
        tasks_id = self._get_ids_from_name(tasks, exec_list)

        best = self._get_best_submissions(courseid, tasks, tasks_id, daterange)
        result = []
        for submission in best:
            result.append(submission["grade"])
        return result

    def _get_before_perfect(self, courseid, tasks, daterange, exec_list, grade_bounds):
        #TODO doc
        tasks_id = self._get_ids_from_name(tasks, exec_list)
        data = self._get_task_failed_attempts(courseid, tasks_id, daterange, grade_bounds)
        return data

    def _get_submissions_per_time(self, courseid, tasks, daterange, exec_list, grade_bounds):
        #TODO doc
        tasks_id = self._get_ids_from_name(tasks, exec_list)
        data = self._get_submissions_by_time(courseid, tasks_id, daterange, grade_bounds)
        return data

    def _get_ids_from_name(self, tasks, exec_list):
        all_tasks_id = []
        for t in tasks:
            if tasks[t]._name.strip() in exec_list:
                all_tasks_id.append(tasks[t].get_id())
        return all_tasks_id

    def GET_AUTH(self, courseid, f=None, t=None):
        """ GET Request """
        # TODO no idea what f and t are
        course, __ = self.get_course_and_check_rights(courseid)
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

        data = None
        statistics = None

        if chart_type == "grades-distribution":
            if all_or_best_submissions == "all":
                data = self._get_all_distribution(courseid, tasks, daterange, exercises, tags)
            else:  # "best
                data = self._get_best_distribution(courseid, tasks, daterange, exercises, tags)

            if data is not None:
                # all_grades = aggregate_all_grades(data)
                all_grades = apply_grade_filter(data, grade_bounds)
                statistics = compute_advanced_stats(all_grades)
                if statistics is not None:
                    statistics["raw_data"] = all_grades

        elif chart_type == "submission-before-perfect":
            data = self._get_before_perfect(courseid, tasks, daterange, exercises, grade_bounds)
            if data is not None:
                all_tries = process_nb_attempts_dict(data)
                statistics = compute_advanced_stats(all_tries)
                if statistics is not None:
                    statistics["raw_data"] = all_tries

        elif chart_type == "submissions-time":
            (times, nb_submissions_per_time) = self._get_submissions_per_time(courseid, tasks, daterange, exercises, grade_bounds)
            statistics = compute_temporal_advanced_stats(nb_submissions_per_time)
            statistics["raw_data"] = nb_submissions_per_time
            statistics["times"] = times
            print("TIMES: " + str(times))
            print("NB: " + str(nb_submissions_per_time))

        if "times" not in statistics:
            statistics["times"] = []  # Placeholder
        print("DB RETURNED")
        print(data)
        print("FINALLY: " + str(statistics))

        course, __ = self.get_course_and_check_rights(courseid)
        return self.template_helper.get_custom_renderer(os.path.join(PATH_TO_PLUGIN, 'templates')).adv_stats(course, chart_query, statistics)


def init(plugin_manager, course_factory, client, plugin_config):  # pylint: disable=unused-argument
    """ Init the plugin """
    plugin_manager.add_page('/admin/([^/]+)/adv_stats', AdvancedCourseStatisticClass)
    plugin_manager.add_hook('course_admin_menu', add_admin_menu)
    plugin_manager.add_page('/plugins/stats/static/(.+)', StaticMockPage)
    plugin_manager.add_hook('css', lambda: '/plugins/stats/static/adv_stats.css')
    plugin_manager.add_hook('javascript_header', lambda: '/plugins/stats/static/adv_stats.js')

