import os
import web

from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage


class AdvancedCourseStatisticClass(INGIniousAdminPage):

    def GET_AUTH(self, courseid, f=None, t=None):
        """ GET Request """

        pass # return the template renderer


def init(plugin_manager, course_factory, client, plugin_config):
    plugin_manager.add_page('/plugins/stats/(.+)', AdvancedCourseStatisticClass)
