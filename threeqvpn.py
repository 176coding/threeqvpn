# encoding:utf-8
import sys, sqlite3, requests, poplib, email, base64, random, time
from flask import Flask, g, render_template
from contextlib import closing

reload(sys)
sys.setdefaultencoding('utf-8')

DATABASE_PATH = '3gvpn_emails.sqlite'
SECRET_KEY = 'ksd241241kndkndk1ndk123442ievjfiee'

app = Flask(__name__)
app.config.from_object(__name__)

host = 'pop3.163.com'
frm = 'master@3qvpn.com'
pwd_list = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u',
            'v', 'w', 'x', 'y', 'z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

headers = {"User-Agent": "    Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0",
           "Host": "www.my3qvpn.org",
           "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
           "Accept-Language": "zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3",
           "Accept-Encoding": "gzip, deflate",
           "Connection": "keep-alive"
}


def connect_db():
    return sqlite3.connect(DATABASE_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    pass


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()


def insert_db():
    with open('mail.txt', 'r') as f:
        for line in f.readlines():
            line_list = line.strip().split('----')
            user, pwd = line_list[0], line_list[1]
            g.db.cursor().execute('insert into emails values(?,?,?,?,?) ',
                                  (None, user, pwd, None, 0)
            )
            pass
        g.db.commit()
        pass

    pass


def query_db(query, args=()):
    cur = g.db.execute(query, args)
    pass


def query_used_unused():
    data = g.db.execute(
        'SELECT  count(*) from emails where used=1 UNION   select count(*) from emails where used=0 ').fetchall()
    if data:
        return data[0][0], data[1][0]
    return None
    pass


def register(user):
    username = user.split('@')[0]
    pwd = ''.join(random.sample(pwd_list, random.randint(5, 9)))
    post_url = 'http://www.my3qvpn.org/register'

    payload = {'username': username, 'email': user, 'password': pwd, 'password1': pwd, 'submit': '免费注册'}

    # make 请求
    req = requests.post(post_url, data=payload, headers=headers)
    print req.text
    if req.text.find(user) != -1:
        print '激活信已发送至邮箱！账号是：', username, '密码是：', pwd
    return username, pwd
    return None
    pass


def get_activate_url(user, pwd):
    pp = poplib.POP3(host)
    pp.set_debuglevel(True)
    pp.user(user)
    pp.pass_(pwd)
    msg_count = pp.stat()[0]
    activate_url = None
    for i in range(msg_count, 0, -1):
        msg_body = pp.retr(i)[1]
        msg_body = '\n'.join([line.decode("utf-8", "ignore") for line in msg_body])
        msg = email.message_from_string(msg_body)
        msg_frm = msg['From']
        print msg_frm
        if frm in msg_frm:
            msg_content = base64.b64decode(msg.get_payload(i=1).get_payload()).decode()
            activate_url = msg_content[msg_content.find('http://www.my3qvpn.org/activate/'):msg_content.find('">')]
            break
            pass
        pass
    pp.quit()
    return activate_url
    pass


def activate_acount(activate_url):
    req = requests.get(activate_url, headers=headers)
    if req.text.find(u'登录成功') != -1:
        print('账号激活成功')
        return True
    return False
    pass


@app.route('/')
@app.route('/index')
def index():
    used, unused = query_used_unused()
    return render_template("index.html", used=used, unused=unused)
    pass


@app.route('/apply')
def apply():
    unused = g.db.execute('select * from emails where used=0 ').fetchone()
    if not unused:
        return '无可用账号'
    username, pwd = register(unused[1])
    g.db.execute('update emails set used=1,vpnpwd=? where id=? ', (pwd, unused[0],))  # 无论下面注册成功与否，都注销掉该账号
    g.db.commit()
    if username:
        i = 0  # 可能出现多线程问题，不知道flask内部是启用多线程还是多进程
        while i < 100:
            i += 1
            time.sleep(1)
            activate_url = get_activate_url(unused[1], unused[2])
            if activate_url:
                break
        ret = activate_acount(activate_url)
        if ret:
            return '注册成功！您的账号是：' + username + '密码是：' + pwd
        pass
    return '注册失败！'
    pass


@app.before_request
def before_request():
    g.db = connect_db()
    # init_db()
    # insert_db()
    pass


@app.after_request
def after_request(response):
    g.db.close()
    return response


if __name__ == '__main__':
    app.run(debug=True)
    # init_db()
    # insert_db()
    # print [chr(i) for i in range(97, 123)]
    pass