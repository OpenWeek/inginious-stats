import os
import web

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
             {"$project": {"taskid": "$taskid", "result": "$result"}},
             {"$group": {"_id": "$taskid", "submissions": {"$sum": 1}, "validSubmissions":
                 {"$sum": {"$cond": {"if": {"$eq": ["$result", "success"]}, "then": 1, "else": 0}}}}
              },
             {"$sort": {"submissions": -1}}])

        return [
            {"name": tasks[x["_id"]].get_name(self.user_manager.session_language()) if x["_id"] in tasks else x["_id"],
             "submissions": x["submissions"],
             "tags": [y[0].get_name() if len(y) == 1 else "" for y in tasks[x["_id"]].get_tags()],
             "validSubmissions": x["validSubmissions"]}
            for x in stats_tasks
        ]

    def _tags_stats(self, courseid, tasks, daterange):
        stats_tasks = self._tasks_stats(courseid, tasks, daterange)

        tag_stats = {}
        for x in stats_tasks:
            for tag in x["tags"]:
                if tag not in tag_stats and tag != "":
                    tag_stats[tag] = {"submissions":x["submissions"], "validSubmissions":x["validSubmissions"]}
                elif tag != "":
                    tag_stats[tag]["submissions"] += x["submissions"]
                    tag_stats[tag]["validSubmissions"] += x["validSubmissions"]
        return tag_stats

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

        stats_tasks = self._tasks_stats(courseid, tasks, daterange)
        stats_tags = self._tags_stats(courseid, tasks, daterange)
        stats_users = self._users_stats(courseid, daterange)
        stats_graph = self._graph_stats(courseid, daterange)

        return self.template_helper.get_custom_renderer(os.path.join(PATH_TO_PLUGIN, 'templates')).adv_stats(course, stats_tags)

    def POST_AUTH(self, courseid):
        """ POST Request"""
        pass


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

