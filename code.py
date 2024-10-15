import requests

cookies = {
    '__jsluid_s': 'ae8072e2dc29168ea95633f6924c7dab',
    'local_': 'zh_CN',
    'parent_qimo_sid_f05eae40-9a31-11e5-83f6-57006c315d67': '8c8215aa-030a-4a0d-a6f0-3c3992883ce5',
    'Hm_lvt_4aae386d5bc1fe5663f87c7fa3369220': '1711033210',
    'clientToken': '018ee73e97788aff7e628ed255f40186',
    'changId': 'fe68bc106f5d4ba22926b9067adf96e5',
    'eln_session_id': 'elnSessionId.7d0ea5b6b9bc4c7cbc22406687be7cfa',
    'corp_code': 'sdnsyh',
    'nxYongdaoIp': '',
    'qimo_seosource_0': '%E7%AB%99%E5%86%85',
    'qimo_seokeywords_0': '',
    'qimo_seosource_f05eae40-9a31-11e5-83f6-57006c315d67': '%E7%AB%99%E5%86%85',
    'qimo_seokeywords_f05eae40-9a31-11e5-83f6-57006c315d67': '',
    'qimo_xstKeywords_f05eae40-9a31-11e5-83f6-57006c315d67': '',
    'href': 'https%3A%2F%2Fsdnsyh.21tb.com%2Fels%2Fhtml%2Findex.parser.do%3Fid%3DNEW_COURSE_CENTER%26current_app_id%3D8a80810f5ab29060015ad1906d0b3811',
    'accessId': 'f05eae40-9a31-11e5-83f6-57006c315d67',
    'learn_eln_session_id': 'learn_eln_session_id.f48a4ca4eb7c4556b8de80333b3a3cda',
    'pageViewNum': '3',
}

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    # 'Cookie': '__jsluid_s=ae8072e2dc29168ea95633f6924c7dab; local_=zh_CN; parent_qimo_sid_f05eae40-9a31-11e5-83f6-57006c315d67=8c8215aa-030a-4a0d-a6f0-3c3992883ce5; Hm_lvt_4aae386d5bc1fe5663f87c7fa3369220=1711033210; clientToken=018ee73e97788aff7e628ed255f40186; changId=fe68bc106f5d4ba22926b9067adf96e5; eln_session_id=elnSessionId.7d0ea5b6b9bc4c7cbc22406687be7cfa; corp_code=sdnsyh; nxYongdaoIp=; qimo_seosource_0=%E7%AB%99%E5%86%85; qimo_seokeywords_0=; qimo_seosource_f05eae40-9a31-11e5-83f6-57006c315d67=%E7%AB%99%E5%86%85; qimo_seokeywords_f05eae40-9a31-11e5-83f6-57006c315d67=; qimo_xstKeywords_f05eae40-9a31-11e5-83f6-57006c315d67=; href=https%3A%2F%2Fsdnsyh.21tb.com%2Fels%2Fhtml%2Findex.parser.do%3Fid%3DNEW_COURSE_CENTER%26current_app_id%3D8a80810f5ab29060015ad1906d0b3811; accessId=f05eae40-9a31-11e5-83f6-57006c315d67; learn_eln_session_id=learn_eln_session_id.f48a4ca4eb7c4556b8de80333b3a3cda; pageViewNum=3',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0',
    'sec-ch-ua': '"Chromium";v="130", "Microsoft Edge";v="130", "Not?A_Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

params = {
    'eln_session_id': 'elnSessionId.7d0ea5b6b9bc4c7cbc22406687be7cfa',
    'courseId': '2894e55d06668a22860beb458ccf4b29',
    'courseType': 'NEW_COURSE_CENTER',
    'vb_server': 'http://21tb-video.21tb.com',
}

response = requests.get(
    'https://sdnsyh.21tb.com/els/html/courseStudyItem/courseStudyItem.loadCourseItemTree.do',
    params=params,
    cookies=cookies,
    headers=headers,
)

print(response.text)
