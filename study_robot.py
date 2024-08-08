import os
import sys
import copy
import json
import time
import datetime
import requests
import configparser

kConfFileName = "main.conf"

def log(info):
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), info)
    sys.stdout.flush()

class Http(object):

    def __init__(self):
        self.session = requests.Session()
        self.eln_session_id = None
        self.headers = { 
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36'
                          ' (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
        }

    @classmethod
    def instance(cls):
        key = "__instance__"
        if hasattr(cls, key):
            return getattr(cls, key)
        else:
            http = Http()
            setattr(cls, key, http)
            return http

    def get_session_id(self):
        return self.session.cookies.get('eln_session_id')

    def post(self, api, params=None, json_ret=True):
        if not params:
            params = {'elsSign': self.get_session_id()}
        else:
            params.update({'elsSign': self.get_session_id()})
        r = self.session.post(api, params, headers=self.headers)
        
        if r.status_code != 200:
            log(f"HTTP request failed with status code {r.status_code}")
        
        if json_ret:
            try:
                return r.json()
            except json.JSONDecodeError as e:
                log(f"Failed to decode JSON response: {e}")
                log(f"Response text: {r.text}")
                raise
        return r.text

    def get(self, api, json_ret=True):
        r = self.session.get(api, params={'elsSign': self.get_session_id()}, headers=self.headers)
        
        if r.status_code != 200:
            log(f"HTTP request failed with status code {r.status_code}")
        
        if json_ret:
            try:
                return r.json()
            except json.JSONDecodeError as e:
                log(f"Failed to decode JSON response: {e}")
                log(f"Response text: {r.text}")
                raise
        return r.text

class ConfigMgr(object):

    def __init__(self):
        self._configer = None
        self.work_dir = os.path.dirname(__file__)
        self.config_file = os.path.join(self.work_dir, kConfFileName)

    def init(self):
        config_file = self.config_file
        if not os.path.exists(self.config_file):
            raise Exception(f"config file {config_file} is missing!")
        self._configer = configparser.ConfigParser()
        readok = self._configer.read(config_file)
        if config_file not in readok:
            raise Exception(f"load config file {config_file} failed")
        log(f"load config {config_file}")

    def get_section_items(self, section):
        if self._configer is not None:
            configs = self._configer.items(section)
            return dict(configs)
        raise Exception("config file not loaded")

class Study(object):

    def __init__(self):
        self.http = Http.instance()
        self.config = ConfigMgr()
        self.config.init()
        self.apis = self.init_api()

    def init_api(self):
        return {
            'login': self._make_api('login'),
            'save_progress': self._make_api('save_progress'),
            'course_item': self._make_api('course_item'),
            'select_resourse': self._make_api('select_resourse'),
            'select_check': self._make_api('select_check'),
            'update_timestep': self._make_api('update_timestep'),
            'course_show': self._make_api('course_show'),
            'heartbeat': self._make_api('heartbeat'),
            'course_center': self._make_api('course_center'),
            'enter_course': self._make_api('enter_course')
        }

    def _make_api(self, api):
        apis_conf = self.config.get_section_items('api')
        if api in apis_conf:
            return f"{apis_conf['host']}{apis_conf[api]}"
        raise Exception(f'api:{api} is not configured')

    def do_login(self):
        main_conf = self.config.get_section_items('main')
        username = main_conf['username']
        password = main_conf['password']
        corpcode = main_conf['corpcode']
        params = {
            'corpCode': corpcode,
            'loginName': username,
            'password': password,
            'returnUrl': '',
            'courseId': '',
            'securityCode': '',
            'continueLogin': 'true'
        }
        r = self.http.post(self.apis['login'], params=params)
        if self.http.get_session_id():
            log(f'user:{username} login success!')
        else:
            msg = r.get('message')
            raise Exception(f"You maybe not login success? e:{msg}")

    def do_heartbeat(self):
        try:
            ret = self.http.post(self.apis['heartbeat'], {'_ajax_toKen': 'os'})
            log(f'do heartbeat, {ret.get("success")}')
        except Exception as e:
            log(f'do heartbeat, {ret.get("failure")}, ret:{str(ret)}')

    def get_my_course(self):
        params = {
            'page.pageSize': '12',
            'page.sortName': 'STUDYTIME',
            'page.pageNo': '1',
            '_': int(time.time())
        }
        try:
            ret = self.http.get(self.apis['course_center'], json_ret=True)
            log('获取课程中心成功')
        except Exception as e:
            log('获取课程中心失败')
        courseListRaw = ret['rows']
        courseList = [i.get('courseId') for i in courseListRaw if i.get('getScoreTime') is None]
        log(f'课程中心共有{len(courseList)}门课程未完成')
        return courseList

    def read_local_studyList(self, course_list):
        if os.path.exists(os.getcwd() + '/21tb/' + 'study.list'):
            log("study.list文件存在, 将优先学习")
            prefreList = []
            with open(os.getcwd() + '/21tb/' + 'study.list', encoding='utf-8') as f:
                for course in f:
                    prefreList.append(course.strip())
            prefreList.extend(course_list)
            return prefreList
        else:
            log("study.list文件不存在将直接学习")
            return course_list

    def get_course_items(self, course_id, pretty=False):
        api = self.apis['course_item'] % course_id
        ret_json = self.http.get(api)
        ret_json = ret_json[0]
        children_list = ret_json['children']
        item_list = []
        for item in children_list:
            if len(item['children']) == 0:
                cell = {
                    'name': item['text'],
                    'scoId': item['id']
                }
                item_list.append(cell)
            else:
                for i in item['children']:
                    cell = {
                        'name': i['text'],
                        'scoId': i['id']
                    }
                    item_list.append(cell)
        if pretty:
            for i in item_list:
                log(f'课程名: {i["name"]} {i["scoId"]}')
            log(f'total items:{len(item_list)}')
        else:
            return item_list

    def select_score_item(self, course_id, score_id):
        params = {
            'courseId': course_id,
            'scoId': score_id,
            'firstLoad': 'true'
        }
        r = self.http.post(self.apis['select_resourse'], params, json_ret=False)
        try:
            location = float(json.loads(r)['location'])
        except:
            location = 0.1
        select_check_api = self.apis['select_check']
        api = select_check_api % (course_id, score_id)
        r = self.http.post(api, json_ret=False)
        return location

    def update_timestep(self):
        ret = self.http.post(self.apis['update_timestep'])
        log(f'do updateTimestepByUserTimmer, {ret.strip().capitalize()}')

    def do_save(self, course_id, score_id, location):
        params = {
            'courseId': '',
            'scoId': '',
            'progress_measure': '100',
            'session_time': '0:0:180',
            'location': '691.1',
            'logId': '',
            'current_app_id': ''
        }
        params.update({'courseId': course_id, 'scoId': score_id, 'location': location})
        r = self.http.post(self.apis['save_progress'], params)
        try:
            if not r:
                params_res = {'courseId': course_id, 'scoId': score_id}
                r = self.http.post(self.apis['select_resourse'], params_res)
                if r.get('isComplete') == 'true':
                    return True
            info = '\033[91m\tcourseProgress: %s\tcompleteRate:%s\tcompleted:%s\t\033[0m' %\
                   (r.get('courseProgress', '-'), r.get('completeRate'), r.get('completed', '-'))
            log(info)
            if r.get('completed', '-') == 'true':
                return True
        except Exception as e:
            log(e)
            log('总进度:\t-\t小节:\t-')
        return False

    def study(self, course_id):
        time_step = 180
        log(f'start course:{course_id}')
        self.http.post(self.apis['enter_course'] % course_id, json_ret=False)
        course_show_api = self.apis['course_show'] % (course_id, self.http.get_session_id())
        log(f'url:{course_show_api}')
        self.http.post(course_show_api, json_ret=False)
        items_list = self.get_course_items(course_id)
        log('*' * 50)
        log(f'共有 {len(items_list)} 个子课程')
        for index, i in enumerate(items_list):
            log(f'{index + 1}、{i["name"]} ')
        log('*' * 50)
        log('begin to start...')
        for index, i in enumerate(items_list):
            sco_id = i['scoId']
            log(f'begin to study:{index + 1}-{i["name"]} {sco_id}')
            location = self.select_score_item(course_id, sco_id)
            cnt = 0
            while True:
                location += time_step * cnt
                cnt += 1
                log(f'location: {location}')
                self.do_heartbeat()
                self.update_timestep()
                ret = self.do_save(course_id, sco_id, location)
                if ret:
                    log(f'{course_id}-{sco_id} done, start next')
                    break
                log(f'*********** study {time_step}s then go on *************')
                time.sleep(time_step)
        info = f'\033[92m\tDONE COURSE, url:{course_show_api}\033[0m'
        log(info)

    def run(self):
        s = time.time()
        self.do_login()
        course_list = self.read_local_studyList(self.get_my_course())
        for course_id in course_list:
            try:
                self.study(course_id)
            except Exception as e:
                log("exception occurred, study next..")
        cost = int(time.time() - s)
        log(f'main end, cost: {cost}s')

if __name__ == '__main__':
    study = Study()
    study.run()
