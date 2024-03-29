#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@Author: Youshumin
@Date: 2019-08-21 11:13:46
@LastEditors: Youshumin
@LastEditTime: 2019-11-13 17:57:09
@Description:  程序启动文件 提供启动停止功能...
'''
import os
import sys

import sentry_sdk
from sentry_sdk.integrations.tornado import TornadoIntegration
from tornado import options

sentry_sdk.init(
    dsn="https://b1696404710445e79550eb272ab9b5c1@sentry.io/1818061",
    integrations=[TornadoIntegration()])


class AppMain:
    def __init__(self):
        PATH_APP_ROOT = os.path.abspath(
            os.path.join(os.path.abspath(os.path.dirname(__file__))))
        if PATH_APP_ROOT not in sys.path:
            sys.path.insert(0, PATH_APP_ROOT)
        options.define("APP_PATH", default=PATH_APP_ROOT, help="app run dir")
        from app import web_app
        self._web_app = web_app()

    def start(self):
        return self._web_app.run()

    def stop(self):
        return self._web_app.stop()


if __name__ == "__main__":
    main = AppMain()
    try:
        main.start()
    except KeyboardInterrupt:
        main.stop()
