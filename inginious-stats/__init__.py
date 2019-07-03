import os
import web
from urllib.parse import parse_qs

from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage
from inginious.common.tags import Tag
from datetime import datetime, date, timedelta

PATH_TO_PLUGIN = os.path.abspath(os.path.dirname(__file__))


def add_admin_menu(course): # pylint: disable=unused-argument
    """ Add a menu for the contest settings in the administration """
    return ('adv_stats', '<i class="fa fa-bar-chart fa-fw"></i>&nbsp; Advanced statistics')


class AdvancedCourseStatisticClass(INGIniousAdminPage):

    def _tasks_stats(self, courseid, tasks, daterange):
        stats_tasks = self.database.submissions.aggregate(
            [{"$match": {"submitted_on": {"$gte": daterange[0], "$lt": daterange[1]}, "courseid": courseid}},
             {"$project": {"taskid": "$taskid", "result": "$result", "tests": "$tests"}},
             {"$group": {"_id": "$taskid", "submissions": {"$sum": 1}, "validSubmissions":
                 {"$sum": {"$cond": {"if": {"$eq": ["$result", "success"]}, "then": 1, "else": 0}}},
                         "tags": {"$first": "$tests"}}
              },
             {"$sort": {"submissions": -1}}])

        return [
            {"_id": x["_id"],
             "name": tasks[x["_id"]].get_name(self.user_manager.session_language()) if x["_id"] in tasks else x["_id"],
             "submissions": x["submissions"],
             "tags": [y for y in x["tags"]],
             "validSubmissions": x["validSubmissions"]}
            for x in stats_tasks
        ]

    def _task_details(self, taskid, daterange):
        task_data =  self.database.submissions.aggregate(
            [{"$match": {"submitted_on": {"$gte": daterange[0], "$lt": daterange[1]}, "taskid": taskid}},
            {"$group": {"_id": "$taskid", "averageGrade": {"$avg": "$grade"},
                         "minGrade": {"$min": "$grade"},"maxGrade": {"$max": "$grade"},
                         "allGrades": {"$push": "$grade"},
                         "submissions": {"$sum": 1}, "validSubmissions":
                 {"$sum": {"$cond": {"if": {"$eq": ["$result", "success"]}, "then": 1, "else": 0}}}}
              }])

        return [{
             "submissions": x["submissions"],
             "averageGrade" : x["averageGrade"],
             "minGrade" : x["minGrade"],
             "maxGrade" : x["maxGrade"],
             "allGrades" : x["allGrades"],
             "validSubmissions": x["validSubmissions"]
                }
            for x in task_data]

    def _task_failed_attempts(self, taskid, daterange):
        task_data =  self.database.submissions.aggregate(
            [{"$match": {"submitted_on": {"$gte": daterange[0], "$lt": daterange[1]}, "taskid": taskid}},
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
        stats_tasks = self._tasks_stats(courseid, tasks, daterange)

        tag_stats = {}
        for x in stats_tasks:
            for tag in x["tags"]:
                if tag not in tag_stats and tag != "":
                    tag_stats[tag] = {  "submissions": x["submissions"], 
                                        "validSubmissions": x["validSubmissions"],
                                        "grade": [x["grade"]]}
                elif tag != "":
                    tag_stats[tag]["submissions"] += x["submissions"]
                    tag_stats[tag]["validSubmissions"] += x["validSubmissions"]
                    tag_stats[tag]["grade"].append(x["grade"])
        return tag_stats

    def _id_stats(self, courseid, tasks, daterange):
        stats_tasks = self._tasks_stats(courseid, tasks, daterange)

        id_stats = {}
        for x in stats_tasks:
            for id_val in x["_id"]:
                if id_val not in id_stats:
                    id_stats[id_val] = {    "submissions":x["submissions"], 
                                            "validSubmissions":x["validSubmissions"],
                                            "grade": [x["grade"]]}
                else:
                    id_stats[id_val]["submissions"] += x["submissions"]
                    id_stats[id_val]["validSubmissions"] += x["validSubmissions"]
                    id_stats[id_val]["grade"].append(x["grade"])
        return id_stats

    def _users_stats(self, courseid, daterange):
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

    def GET_AUTH(self, courseid, f=None, t=None):
        """ GET Request """
        course, __ = self.get_course_and_check_rights(courseid)
        # TODO: Remove stats in get
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

        stats_tasks = self._task_failed_attempts("s2_make", daterange)
        return self.template_helper.get_custom_renderer(os.path.join(PATH_TO_PLUGIN, 'templates')).adv_stats(course, None)

    def POST_AUTH(self, courseid):
        """ POST Request"""
        print("=============>> POST was called (return the same thing as GET)")
        data = web.input(stats_from='', stats_to='', chart_type='', submissions_filter='', max_submission_grade='', min_submission_grade='', filter_tags='', filter_exercises='')
        print("DATA: " + str(data))

        # TODO this is copied from GET_AUTH
        course, __ = self.get_course_and_check_rights(courseid)
        return self.template_helper.get_custom_renderer(os.path.join(PATH_TO_PLUGIN, 'templates')).adv_stats(course, data)


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

