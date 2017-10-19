import re 
from pymysql import *


# 全局变量动态资源文件的存放路径
TEMPLATES_ROOT = './templates'

URL=dict()
'''
 定义一个字典,来记录浏览器请求不一样的资源的时候，调用哪个函数为这个请求服务
 '/index.html':index
    '/center.html':center
'''
def route(url):
    def set_func(func):
        URL[url] = func
        def call_func(file_name):
            return func(file_name)
        return call_func
    return set_func


@route(r'/center\.html$')
def center(file_name,url):
    '''请求center.html的文件 该函数运行'''
    try:
        f = open(TEMPLATES_ROOT + file_name)
    except Exception as ret:
        return '异常%s' %ret
    else:
        content = f.read()
        f.close()
        # 连接数据库
        conn = connect(host='localhost',port=3306,user='root',password='mysql',database='stock_db',charset='utf8')
        # 获取cursor对象
        cursor = conn.cursor()
        sql='select i.code, i.short, i.chg, i.turnover, i.price, i.highs,f.note_info from info as i inner join focus as f on f.info_id=i.id;'
        cursor.execute(sql)
        data_from_mysql = cursor.fetchall()
        cursor.close()
        conn.close()
        html_tr = """
            <tr>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>
                    <a type="button" class="btn btn-default btn-xs" href="/update/%s.html"> <span class="glyphicon glyphicon-star" aria-hidden="true"></span> 修改 </a>
                </td>
                <td>
                    <input type="button" value="删除" id="toDel" name="toDel" systemidvaule="%s">
                </td>
            </tr>"""


            
        http = ''
        for temp in data_from_mysql:
            http+=html_tr %(temp[0],temp[1],temp[2],temp[3],temp[4],temp[5],temp[6],temp[0],temp[0])
        
        content=re.sub(r'\{%content%\}', http, content)        
        return content


@route(r'/index\.html$')
def index(file_name,url):
    '''请求index.html的文件 该函数运行'''
    try:
        f = open(TEMPLATES_ROOT + file_name)
    except Exception as ret:
        return '异常%s' %ret
    else:
        content = f.read()
        f.close()
        # 连接数据库
        conn = connect(host='localhost',port=3306,user='root',password='mysql',database='stock_db',charset='utf8')
        # 获取cursor对象
        cursor = conn.cursor()
        sql='select * from info'
        cursor.execute(sql)
        data_from_mysql = cursor.fetchall()
        cursor.close()
        conn.close()
        html_tr = """
            <tr>
                <td>%s</td>
                <td>%s</td> 
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>
                    <input type="button" value="添加" id="toAdd" name="toAdd" systemidvaule="%s">
                </td>
            </tr>
            """
        http = ''
        for temp in data_from_mysql:
            http+=html_tr %(temp[0],temp[1],temp[2],temp[3],temp[4],temp[5],temp[6],temp[7],temp[1])
        
        content=re.sub(r'\{%content%\}', http, content)        
        return content

@route(r'/add/(\d+)\.html$')
def add(file_name, url):
    '''关注某一个股票'''
    ret=re.match(url,file_name)
    if ret:
        stock_code=ret.group(1)
    else:
        stock_code = '0'
        return '数据有误'
    conn = connect(host='localhost',port=3306,user='root',password='mysql',database='stock_db',charset='utf8')
    cursor = conn.cursor()
    sql='''select * from focus where info_id= (select id from info where code=%s);'''
    cursor.execute(sql, [stock_code])
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return '关注失败 已经存在!'
    
    try:
       
        sql='''insert into focus (info_id) select id from info where code=%s;'''
        data_from_mysql = cursor.execute(sql, [stock_code])
        conn.commit()
        

    except Exception as ret:
        result_info = '关注失败' , ret

    else:
        result_info = '关注成功'

    finally:
        cursor.close()
        conn.close()
        return result_info

@route(r'/del/(\d+)\.html$')
def delete(file_name, url):
    '''取消关注某一个股票'''
    ret=re.match(url,file_name)
    if ret:
        stock_code=ret.group(1)
    else:
        stock_code = '0'
        return '数据有误'

    
    conn = connect(host='localhost',port=3306,user='root',password='mysql',database='stock_db',charset='utf8')    
    cursor = conn.cursor()
    try:
        sql='''delete from focus where info_id = (select id from info where code=%s);''' 
        cursor.execute(sql, [stock_code])
        conn.commit()

    except Exception as ret:
        result_info = '取消失败%s' %ret
    
    else:
        result_info = '取消关注成功'

    finally:
        
        cursor.close()
        conn.close()
        return result_info


@route(r'/update/(\d+)\.html$')
def update(file_name,url):
    '''显示update页面1'''
     
    ret=re.match(url,file_name)
    if ret:
        stock_code=ret.group(1)
    else:
        stock_code = '0'
        return '数据有误'
    try:
        f = open(TEMPLATES_ROOT+'/update.html')    
    except Exception as ret:
        return '产生异常',ret
    else:
        content = f.read()
        f.close()

        conn = connect(host='localhost',port=3306,user='root',password='mysql',database='stock_db',charset='utf8')
        cursor = conn.cursor()
        sql = """select note_info from focus where info_id = (select id from info where code=%s)"""
        cursor.execute(sql, [stock_code])
        note_info = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        content = re.sub(r"\{%code%\}", stock_code, content)
        content = re.sub(r"\{%note_info%\}", note_info, content)

        return content
# /uodate/123321/hhh.html
@route(r'/update/(\d+)/(.+)\.html$')
def update(file_name,url):
    '''显示update页面1'''
    ret = re.match(url, file_name)
    if ret:
        stock_code = ret.group(1)
        note_info = ret.group(2)
        # 解url的编码
        note_info = urllib.parse.unquote(note_info)
    else:
        return "数据有误...."

    try:
        conn = connect(host='localhost',port=3306,user='root',password='mysql',database='stock_db',charset='utf8')
        cursor = conn.cursor()
        sql = """update focus set note_info = %s where info_id = (select id from info where code=%s);"""
        cursor.execute(sql, [note_info, stock_code])
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as ret:
        return "修改失败...%s" % ret
    else:
        return "修改成功....."


# URL['/index.py'] = index
# URL['/center.py'] = center
def app(env, start_response):
    start_response('200 OK',[('Content-Type','text/html;charset=utf-8')])
    file_name = env['path_info']
    try:
        for url, func in  URL.items():
            # url-->r'add/\d+\.html$
            # file_name --->/add/12313.html
            ret = re.match(url,file_name)
            if ret:
                return func(file_name, url)
        else:
            return '请求页面不存在 404'
            
    except Exception as ret:
        return "产生了异常。。。异常信息是：" ,ret



