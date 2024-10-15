import os
import sys
import json
import time
import datetime
import requests
import configparser
import traceback
from bs4 import BeautifulSoup

CONFIG_FILE_NAME = "main.conf"

def log(info):
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), info)
    sys.stdout.flush()

class HttpClient:
    def __init__(self):
        self.session = requests.Session()
        self.eln_session_id = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
        }

    @classmethod
    def get_instance(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = cls()
        return cls._instance

    def get_session_id(self):
        return self.session.cookies.get('eln_session_id')

    def post(self, api, params=None):
        if not params:
            params = {'elsSign': self.get_session_id()}
        else:
            params.update({'elsSign': self.get_session_id()})
        response = self.session.post(api, params, headers=self.headers)
        
        if response.status_code != 200:
            log(f"HTTP POST request to {api} failed with status code {response.status_code}")
        
        return response

    def get(self, api):
        response = self.session.get(api, params={'elsSign': self.get_session_id()}, headers=self.headers)
        
        if response.status_code != 200:
            log(f"HTTP GET request to {api} failed with status code {response.status_code}")
        
        return response

    @staticmethod
    def get_json(response):
        try:
            return response.json()
        except json.JSONDecodeError:
            log(f"Failed to decode JSON. Response content: {response.text[:200]}...")
            return None

class ConfigManager:
    def __init__(self):
        self._config = None
        self.work_dir = os.path.dirname(__file__)
        self.config_file_path = os.path.join(self.work_dir, CONFIG_FILE_NAME)

    def initialize(self):
        if not os.path.exists(self.config_file_path):
            raise Exception(f"Config file {self.config_file_path} is missing!")
        self._config = configparser.ConfigParser()
        read_ok = self._config.read(self.config_file_path, encoding='utf-8')
        if self.config_file_path not in read_ok:
            raise Exception(f"Failed to load config file {self.config_file_path}")
        log(f"Loaded config {self.config_file_path}")

    def get_section_items(self, section):
        if self._config is not None:
            configs = self._config.items(section)
            return dict(configs)
        raise Exception("Config file not loaded")

class StudyBot:
    def __init__(self):
        self.http = HttpClient.get_instance()
        self.config = ConfigManager()
        self.config.initialize()
        self.apis = self.init_api()

    def init_api(self):
        return {
            'login': self._make_api('login'),
            'save_progress': self._make_api('save_progress'),
            'course_item': self._make_api('course_item'),
            'select_resource': self._make_api('select_resource'),  # 修正拼写
            'select_check': self._make_api('select_check'),
            'update_timestep': self._make_api('update_timestep'),
            'course_show': self._make_api('course_show'),
            'heartbeat': self._make_api('heartbeat'),
            'course_center': self._make_api('course_center'),
            'enter_course': self._make_api('enter_course')
        }

    def _make_api(self, api):
        api_config = self.config.get_section_items('api')
        if api in api_config:
            return f"{api_config['host']}{api_config[api]}"
        log(f'Warning: API:{api} is not configured')
        return None

    def login(self):
        main_config = self.config.get_section_items('main')
        username = main_config['username']
        password = main_config['password']
        corp_code = main_config['corpcode']
        params = {
            'corpCode': corp_code,
            'loginName': username,
            'password': password,
            'returnUrl': '',
            'courseId': '',
            'securityCode': '',
            'continueLogin': 'true'
        }
        response = self.http.post(self.apis['login'], params=params)
        result = self.http.get_json(response)
        if self.http.get_session_id():
            log(f'User:{username} login successful!')
        else:
            msg = result.get('message') if result else "Unknown error"
            raise Exception(f"Login might have failed. Error: {msg}")

    def send_heartbeat(self):
        try:
            response = self.http.post(self.apis['heartbeat'], {'_ajax_toKen': 'os'})
            result = self.http.get_json(response)
            if result:
                log(f'Heartbeat sent, success: {result.get("success", False)}')
            else:
                log(f'Heartbeat sent, but unable to parse response. Status code: {response.status_code}')
        except Exception as e:
            log(f'Heartbeat failed. Error: {str(e)}')

    def get_my_courses(self):
        params = {
            'page.pageSize': '12',
            'page.sortName': 'STUDYTIME',
            'page.pageNo': '1',
            '_': int(time.time())
        }
        try:
            response = self.http.get(self.apis['course_center'])
            if response.status_code == 200:
                try:
                    result = response.json()
                    log('Successfully retrieved course center')
                    course_list_raw = result.get('rows', [])
                    course_list = [i.get('courseId') for i in course_list_raw if i.get('getScoreTime') is None]
                    log(f'Course center has {len(course_list)} unfinished courses')
                    return course_list
                except json.JSONDecodeError:
                    log(f"Failed to parse JSON from course center response. Content: {response.text[:200]}...")
                    return []
            else:
                log(f"Failed to retrieve course center. Status code: {response.status_code}")
                return []
        except Exception as e:
            log(f'Failed to retrieve course center: {str(e)}')
            return []

    def read_local_study_list(self, course_list):
        study_list_path = os.path.join(os.getcwd(), '21tb', 'study.list')
        if os.path.exists(study_list_path):
            log("study.list file exists, will prioritize these courses")
            prefer_list = []
            with open(study_list_path, encoding='utf-8') as f:
                for course in f:
                    prefer_list.append(course.strip())
            prefer_list.extend(course_list)
            return prefer_list
        else:
            log("study.list file does not exist, will study directly")
            return course_list

    def get_course_items(self, course_id, pretty=False):
        api = self._build_api_url('course_item', course_id=course_id, session_id=self.http.get_session_id())
        log(f"Requesting course items from: {api}")
        response = self.http.get(api)
        log(f"Response status code: {response.status_code}")
        log(f"Response headers: {response.headers}")
        
        try:
            content_type = response.headers.get('Content-Type', '')
            log(f"Content-Type: {content_type}")
            
            if 'text/html' in content_type:
                # Parse HTML content
                soup = BeautifulSoup(response.text, 'html.parser')
                items_list = []
                for item in soup.select('.cl-catalog-item-sub a'):
                    items_list.append({
                        'name': item.get('title', ''),
                        'scoId': item.get('data-id', '')
                    })
            else:
                # Attempt to parse as JSON (existing logic)
                ret_json = response.json()
                ret_json = ret_json[0]
                children_list = ret_json.get('children', [])
                items_list = []
                for item in children_list:
                    if len(item.get('children', [])) == 0:
                        cell = {
                            'name': item.get('text', ''),
                            'scoId': item.get('id', '')
                        }
                        items_list.append(cell)
                    else:
                        for i in item.get('children', []):
                            cell = {
                                'name': i.get('text', ''),
                                'scoId': i.get('id', '')
                            }
                            items_list.append(cell)
            
            if pretty:
                for i in items_list:
                    log(f'Course name: {i["name"]} {i["scoId"]}')
                log(f'Total items: {len(items_list)}')
            else:
                return items_list
        except Exception as e:
            log(f"Error in get_course_items: {str(e)}")
            log(f"Response content: {response.text[:500]}...")  # 只打印前500个字符
            return []

    def select_score_item(self, course_id, score_id):
        params = {
            'courseId': course_id,
            'scoId': score_id,
            'firstLoad': 'true'
        }
        r = self.http.post(self.apis['select_resource'], params)
        try:
            location = float(json.loads(r.text)['location'])
        except:
            location = 0.1
        
        # 修改这里
        select_check_api = self.apis['select_check']
        if '{courseId}' in select_check_api and '{scoId}' in select_check_api:
            api = select_check_api.format(courseId=course_id, scoId=score_id)
        elif '%s' in select_check_api:
            api = select_check_api % (course_id, score_id)
        else:
            api = select_check_api.replace('{0}', course_id).replace('{1}', score_id)
        
        r = self.http.post(api)
        print(location)
        return location

    def update_timestep(self):
        try:
            response = self.http.post(self.apis['update_timestep'])
            if response.status_code == 200:
                result = response.text.strip()
                log(f'Updated timestep, {result.capitalize()}')
            else:
                log(f'Failed to update timestep. Status code: {response.status_code}')
        except Exception as e:
            log(f'Error updating timestep: {str(e)}')

    def save_progress(self, course_id, score_id, location):
        params = {
            'courseId': course_id,
            'scoId': score_id,
            # 'progress_measure': '400',
            'progress_measure': '100',
            'session_time': '0:0:180',
            'location': location,
            'logId': '',
            'current_app_id': ''
        }
        params.update({'courseId': course_id, 'scoId': score_id, 'location': location})
        r = self.http.post(self.apis['save_progress'], params)
        try:
            result = self.http.get_json(r)
            if not result:
                params_res = {'courseId': course_id, 'scoId': score_id}
                r = self.http.post(self.apis['select_resource'], params_res)
                result = self.http.get_json(r)
                if result and result.get('isComplete') == 'true':
                    return True
            info = '\033\tcourseProgress: %s\tcompleteRate: %s\tcompleted: %s\t\033' %\
                   (result.get('courseProgress', '-'), result.get('completeRate'), result.get('completed', '-'))
            log(info)
            if result and result.get('completed', '-') == 'true':
                return True
        except Exception as e:
            log(f"Error in save_progress: {str(e)}")
            log('Total progress:\t-\tSection:\t-')
        return False

    def _build_api_url(self, api_name, **kwargs):
        try:
            base_url = self.apis[api_name]
            for key, value in kwargs.items():
                placeholder = '{' + key + '}'
                if placeholder in base_url:
                    base_url = base_url.replace(placeholder, str(value))
            return base_url
        except KeyError as e:
            log(f"API '{api_name}' not found in configuration")
            raise
        except Exception as e:
            log(f"Error building URL for API '{api_name}': {str(e)}")
            raise

    def study_course(self, course_id):
        log(f"Starting course: {course_id}")
        log(f"Session ID: {self.http.get_session_id()}")
        
        enter_course_url = self._build_api_url('enter_course', course_id=course_id)
        log(f"Enter course URL: {enter_course_url}")
        
        try:
            enter_course_response = self.http.post(enter_course_url)
            log(f"Enter course response status: {enter_course_response.status_code}")
            log(f"Enter course response content: {enter_course_response.text[:200]}...")
            if enter_course_response.status_code != 200:
                log(f"Failed to enter course. Status code: {enter_course_response.status_code}")
                return
        except Exception as e:
            log(f"Error entering course: {str(e)}")
            return

        course_show_url = self._build_api_url('course_show', course_id=course_id, session_id=self.http.get_session_id())
        log(f'Course show URL: {course_show_url}')
        
        try:
            course_show_response = self.http.post(course_show_url)
            log(f"Course show response status: {course_show_response.status_code}")
            log(f"Course show response content: {course_show_response.text[:200]}...")
            if course_show_response.status_code != 200:
                log(f"Failed to show course. Status code: {course_show_response.status_code}")
                return
        except Exception as e:
            log(f"Error in course show: {str(e)}")
            return

        items_list = self.get_course_items(course_id)
        if not items_list:
            log(f"No course items found for course {course_id}")
            return

        # time_step = 10
        time_step = 180
        try:
            log('*' * 50)
            log(f'Total of {len(items_list)} sub-courses')
            for index, i in enumerate(items_list):
                log(f'{index + 1}. {i["name"]} ')
            log('*' * 50)
            log('Beginning to study...')

            for index, i in enumerate(items_list):
                sco_id = i['scoId']
                log(f'Starting to study: {index + 1}-{i["name"]} {sco_id}')
                location = self.select_score_item(course_id, sco_id)
                cnt = 0
                while True:
                    location += time_step * cnt
                    cnt += 1
                    log(f'Location: {location}')
                    self.send_heartbeat()
                    self.update_timestep()
                    ret = self.save_progress(course_id, sco_id, location)
                    if ret:
                        log(f'{course_id}-{sco_id} completed, starting next')
                        break
                    log(f'*********** Studied for {time_step}s, continuing *************')
                    # time.sleep(time_step/10)
                    time.sleep(time_step)
            log(f'\033[92m\tCOURSE COMPLETED, URL: {course_show_url}\033[0m')
        except Exception as e:
            log(f"Error in study_course for course_id {course_id}: {str(e)}")
            import traceback
            log(traceback.format_exc())

    def run(self):
        start_time = time.time()
        try:
            self.login()  # 初始登录
            course_list = self.read_local_study_list(self.get_my_courses())
            for course_id in course_list:
                try:
                    # self.login()  # 在每个课程开始前重新登录
                    self.study_course(course_id)
                except Exception as e:
                    log(f"Exception occurred while studying course {course_id}: {str(e)}")
                    log(f"Error details: {type(e).__name__}")
                    import traceback
                    log(traceback.format_exc())
        except Exception as e:
            log(f"Critical error in main process: {str(e)}")
            log(f"Error details: {type(e).__name__}")
            import traceback
            log(traceback.format_exc())
        finally:
            duration = int(time.time() - start_time)
            log(f'Main process ended, duration: {duration}s')

if __name__ == '__main__':
    study_bot = StudyBot()
    study_bot.run()