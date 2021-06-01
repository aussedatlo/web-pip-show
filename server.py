#!/usr/bin/env python3

import requests
import socketserver
import http.server
import json
import collections

STATUS = {
    "success": 9,
    "skipped": 8,
    "canceled": 7,
    "created": 6,
    "build": 5,
    "running": 4,
    "started": 3,
    "pending": 2,
    "failed": 1,
    "undefined": 0
}

CACHE_ID = ""
CACHE_HTML = ""

try:
    f = open("config.json", "r")
    CONFIG = json.loads(f.read())["config"]
    TOKEN = CONFIG["token"]
    GITLAB_PIP_URL = CONFIG["url"] + "/api/v4/projects/" + CONFIG["id"] + "/pipelines"
    GITLAB_PIP_JOB_URL = GITLAB_PIP_URL + "/:pipeline_id/jobs?per_page=40"
    GITLAB_JOB_URL = CONFIG["url"] + "/api/v4/projects/" + CONFIG["id"] + "/jobs"
    SIZE = int(CONFIG["size"])
    PORT = int(CONFIG["port"])
except:
    print("config file is invalid")
    exit(-1)

def get_status_from_id(id):
    """
    get_status_from_id: get string status from int value

    :param val: id value
    """
    for key, value in STATUS.items():
        if id == value:
            return key
    return "undefined"

def get_pipeline_list(page):
    """
    get_pipeline_list: get list of pipeline by page

    :param page: page to request, one page contains by default 20 pipelines
    """
    print("get_pipeline_list: page: " + str(page))
    header = {'PRIVATE-TOKEN': TOKEN}
    url = GITLAB_PIP_URL
    url += "?page=" + str(page)
    r = requests.get(url, headers=header)
    return json.loads(r.text)

def get_pipeline_job_list(pip_id):
    """
    get_pipeline_job_list: get json formatted job list of specific pipeline

    :param pip_id: pipeline id
    """
    header = {'PRIVATE-TOKEN': TOKEN}
    url = GITLAB_PIP_JOB_URL.replace(":pipeline_id", str(pip_id))
    r = requests.get(url, headers=header)
    return json.loads(r.text)

def get_job_list():
    """
    get_pipeline_job_list: get json formatted job list of project
    """
    header = {'PRIVATE-TOKEN': TOKEN}
    url = GITLAB_JOB_URL
    r = requests.get(url, headers=header)
    return json.loads(r.text)

def get_template(template):
    """
    get_template: get template html file
    """
    f = open("template/" + template + ".html", "r")
    return f.read()

def template_replace(template, s, elem):
    str_replace = "{" + s + "}"
    return template.replace(str_replace, str(elem[s]))

class Handler(http.server.SimpleHTTPRequestHandler):

    def send_header_ok(self,):
        """
        send_header_ok: send header result code 200
        """
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def send_header_nok(self, val):
        """
        send_header_nok: send error header

        :param val: error code value
        """
        self.send_response(val)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def get_stage_list(self, pip_id):
        """
        get_stage_list: get list of all stages with merged status

        :param pip_id: pipeline id
        """
        stage_list = collections.OrderedDict()
        jobs = get_pipeline_job_list(pip_id)
        for job in reversed(jobs):

            stage = job["stage"]
            status = job["status"]

            if (stage in stage_list.keys()):
                stage_list[stage] = min(STATUS[status], stage_list[stage])
            else:
                stage_list[stage] = STATUS[status]
        return stage_list

    def get_html_stage_list(self, stage_list):
        """
        get_html_stage_list: get html of all stages from a pipeline

        :param stage_list: list of all stages from a pipeline with merged status
        """
        main_td = ""
        for stage in stage_list:

            td = get_template("td")
            td = td.replace("{status}", get_status_from_id(stage_list[stage]))
            td = td.replace("{name}", stage)

            main_td += td
        return main_td

    def get_html_pipeline(self, pipeline):
        """
        get_html_pipeline: create html from template for pipeline element

        :param pipeline: json pipeline element
        """
        main_tr = ""
        tr = get_template("tr")
        tr = template_replace(tr, "id", pipeline)
        tr = template_replace(tr, "status", pipeline)
        tr = template_replace(tr, "ref", pipeline)

        stage_list = self.get_stage_list(pipeline["id"])
        main_td = self.get_html_stage_list(stage_list)

        main_tr += tr
        main_tr = main_tr.replace("{td}", main_td)
        return main_tr

    def verify_cache(self):
        global CACHE_HTML
        global CACHE_ID
        """
        verify_cache: request gitlab and create html page
        """
        jobs_list_str = json.dumps(get_job_list())
        if CACHE_ID == jobs_list_str:
            return True
        else:
            print("verify_cache: save in cache")
            CACHE_ID = jobs_list_str
            return False

    def get_html(self):
        global CACHE_HTML
        global CACHE_ID
        """
        get_html: request gitlab and create html page
        """
        ref_list = []
        main_tr = ""
        page = 0
        main = get_template("main")

        if (self.verify_cache()):
            print("get_html: cache id matched, use html cache")
            return CACHE_HTML

        # process until we have SIZE branches to display
        while len(ref_list) < SIZE:

            page += 1
            pipeline_list = get_pipeline_list(page)

            for pip in pipeline_list:

                # all branches are found, leave
                if len(ref_list) >= SIZE:
                    print("get_html: break")
                    break

                # keep only the last result of a branch
                if pip["ref"] in ref_list:
                    continue

                ref_list.append(pip["ref"])
                print("get_html: pipelines branch found:" + str(len(ref_list)))

                main_tr += self.get_html_pipeline(pip)

        main = main.replace("{table}", main_tr)
        CACHE_HTML = main
        return main

    def do_GET(self):
        """
        do_GET: serve a GET request
        """
        print("do_GET: path: " + self.path)

        # ignore favicon
        if (self.path == "/favicon.ico"):
            self.send_header_nok(404)
            return

        try:
            main = self.get_html()
            self.send_header_ok()
        except TypeError as e:
            print(e)
            main = "404 not found"
            self.send_header_nok(404)
        except Exception as e:
            print(e)
            main = get_template("error")
            self.send_header_nok(500)

        self.wfile.write(main.encode("utf-8"))

httpd = socketserver.TCPServer(("", PORT), Handler)
print("serving at port", PORT)
httpd.serve_forever()
