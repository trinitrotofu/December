from blog.models import Option, Post, Comment, Media
from . import settings
import os, markdown, time, hashlib, urllib.parse, json, hashlib, requests

def set_option(name, value):
    try:
        obj = Option.objects.get(name=name)
        obj.value = value
        obj.save()
    except Option.DoesNotExist:
        Option(name=name, value=value).save()

def get_option(name):
    try:
        return Option.objects.get(name=name).value
    except Option.DoesNotExist:
        return ""

def get_advanced_option(name, default=None):
    try:
        return json.loads(get_option("advanced_settings")).get(name, default)
    except:
        return default

def get_site_icon():
    return get_advanced_option("icon", "/static/img/icon_m.png")

def get_navigation_links():
    return get_advanced_option("menu", [])

def get_admin_navigation_links():
    return [
            ['<i class="tachometer alternate icon"></i>Dashboard', "/admin"],
            ['<i class="images icon"></i>Media Library', "/admin/media"],
            ['<i class="cog icon"></i>Settings', "/admin/settings"],
            ['<i class="sign out alternate icon"></i>Sign out', "/logout"]
        ]

def post_exist(pid):
    return Post.objects.filter(id=pid).count() != 0

def save_post(pid, data):
    obj = None
    if pid == 0:
        obj = Post()
    else:
        obj = Post.objects.get(id=pid)
    obj.title = data["title"]
    obj.text = data["text"]
    obj.post_type = data["type"]
    obj.protected = data["protected"]
    obj.password = data["password"]
    obj.is_top = data["top"]
    obj.allow_comment = data["allow_comment"]
    obj.post_time = data["time"]
    obj.save()
    return obj.id

def delete_post(pid):
    Post.objects.get(id = pid).delete()
    Comment.objects.filter(pid=pid).delete()

def get_post_data(pid):
    obj = Post.objects.get(id=pid)
    return {
        "title": obj.title,
        "text": obj.text,
        "type": obj.post_type,
        "protected": obj.protected,
        "password": obj.password,
        "top": obj.is_top,
        "allow_comment": obj.allow_comment,
        "comments_num": obj.comments_num,
        "time": obj.post_time,
    }

def get_post_list(x, y, check_top = False,
        logged_in = False, session = {}, search = ""):
    tmp = Post.objects.filter(post_type="post")
    search_list = search.split()
    if len(search_list) > 0:
        title_set = tmp.all()
        text_set = tmp.all()
        if not logged_in:
            text_set = text_set.filter(protected = False)
        for s in search_list:
            title_set = title_set.filter(title__icontains = s)
            text_set = text_set.filter(text__icontains = s)
        tmp = title_set | text_set
    if check_top:
        tmp = tmp.order_by("-is_top", "-post_time")
    else:
        tmp = tmp.order_by("-post_time")
    res = []
    x = max(min(x, tmp.count()), 0)
    y = max(min(y, tmp.count()), 0)
    while x < y:
        obj = tmp[x]
        x += 1
        d = {
            "pid": obj.id,
            "title": obj.title,
            "text": obj.text,
            "protected": obj.protected,
            "top": obj.is_top,
            "comments_num": obj.comments_num,
            "time": obj.post_time,
        }
        if obj.protected and not logged_in and obj.password != \
                session.get("post_pswd_of_" + str(obj.id), None):
            d["text"] = "The content is password protected."
            d["comments_num"] = 0
        res.append(d)
    return (tmp.count(), res)

def md2post(content):
    return markdown.markdown(
        content,
        extensions = [
            'markdown.extensions.extra',
            'markdown.extensions.codehilite',
            'mdx_math',
        ],
        extension_configs = {
            'mdx_math': {'enable_dollar_delimiter': True},
        }
    )

def get_abstract(html):
    idx = html.find("<!--more-->")
    if idx == -1:
        return html
    return html[:idx]

def get_pagination(num, page_size, post_list_len, get_str = ""):
    page_cnt = post_list_len
    if page_cnt % page_size > 0:
        page_cnt = page_cnt // page_size + 1
    else:
        page_cnt = page_cnt // page_size
    if page_cnt <= 1:
        return []
    res = [(str(num), "", "active", "div")]
    if num > 2:
        url = "/page/" + str(num - 1) + get_str
        res.insert(0, (str(num - 1), url, "", "a"))
    if num < page_cnt - 1:
        url = "/page/" + str(num + 1) + get_str
        res.append((str(num + 1), url, "", "a"))
    if num > 3:
        res.insert(0, ("...", "", "disabled", "div"))
    if num < page_cnt - 2:
        res.append(("...", "", "disabled", "div"))
    if num > 1:
        res.insert(0, ("1", "/page/1" + get_str, "", "a"))
    if num < page_cnt:
        url = "/page/" + str(page_cnt) + get_str
        res.append((str(page_cnt), url, "", "a"))
    return res

def timestamp2str(ts):
    now = int(time.time())
    d = now - ts
    res = ""
    suf = " ago"
    if d < 0:
        suf = " later"
        d = -d
    seq = (
        (31536000, "year"),
        (2592000, "month"),
        (604800, "week"),
        (86400, "day"),
        (3600, "hour"),
        (60, "minute"),
        (1, "second")
    )
    for s in seq:
        if d >= s[0]:
            x = d // s[0]
            res = str(x)
            if x > 1:
                res += " " + s[1] + "s "
            else:
                res += " " + s[1] + " "
            break
    if res == "":
        res = "Just now"
    else:
        res += suf
    return res

def get_email_hash(email):
    email = email.strip().lower()
    return hashlib.md5(email.encode('utf-8')).hexdigest()

def comment_exist(cid):
    return Comment.objects.filter(id=cid).count() != 0

def get_comment_data(cid):
    obj = Comment.objects.get(id=cid)
    author = obj.author
    email = obj.email
    if obj.is_admin:
        author = get_option("username")
        email = get_option("email")
    return {
        "author": author,
        "email": email,
        "is_admin": obj.is_admin,
        "url": obj.url,
        "text": obj.text,
        "pid": obj.pid,
        "parent": obj.parent,
        "status": obj.status,
        "time": obj.comment_time,
    }

def save_comment(cid, data):
    obj = None
    if cid == 0:
        obj = Comment()
    else:
        obj = Comment.objects.get(id=cid)
    if not data["is_admin"]:
        obj.author = data["author"]
        obj.email = data["email"]
    else:
        obj.author = ""
        obj.email = ""
    obj.is_admin = data["is_admin"]
    obj.url = data["url"]
    obj.text = data["text"]
    obj.pid = data["pid"]
    obj.parent = data["parent"]
    obj.status = data["status"]
    obj.comment_time = data["time"]
    obj.save()
    if cid == 0:
        post = Post.objects.get(id=obj.pid)
        post.comments_num += 1
        post.save()
    return obj.id

def delete_comment(cid):
    tmp = Comment.objects.filter(parent=cid)
    for i in tmp:
        delete_comment(i.id)
    obj = Comment.objects.get(id=cid)
    post_obj = Post.objects.get(id=obj.pid)
    post_obj.comments_num -= 1
    post_obj.save()
    obj.delete()

def build_comment_tree(res, qset, cid, username, user_email_hash):
    tmp = qset.filter(parent=cid).order_by("-comment_time")
    if tmp.count() == 0:
        return
    for i in tmp:
        children = []
        build_comment_tree(children, qset, i.id, username, user_email_hash)
        author = i.author
        url = i.url
        email_hash = None
        if i.is_admin:
            author = username
            url = "/"
            email_hash = user_email_hash
        else:
            email_hash = get_email_hash(i.email)
        res.append({
            "cid": i.id,
            "author": author,
            "url": url,
            "time": timestamp2str(i.comment_time),
            "is_admin": i.is_admin,
            "text": i.text,
            "email_hash": email_hash,
            "children": children,
        })

def get_comments_with_pid(pid):
    tmp = Comment.objects.filter(pid=pid).filter(status="published")
    res = []
    build_comment_tree(
        res = res,
        qset = tmp,
        cid = 0,
        username = get_option("username"),
        user_email_hash = get_email_hash(get_option("email"))
    )
    return res

def get_recent_comment_list(size):
    tmp = Comment.objects.filter(status="published").order_by("-comment_time")
    res = []
    x = 0
    y = max(min(size, tmp.count()), 0)
    username = get_option("username")
    user_email_hash = get_email_hash(get_option("email"))
    while x < y:
        obj = tmp[x]
        x += 1
        post_data = get_post_data(obj.pid)
        if not post_data["allow_comment"] \
                or post_data["type"] == "draft" \
                or post_data["protected"]:
            if y < tmp.count():
                y += 1
            continue
        author = obj.author
        email_hash = None
        if obj.is_admin:
            author = username
            email_hash = user_email_hash
        else:
            email_hash = get_email_hash(obj.email)
        text = obj.text
        if len(text) > 98:
            text = text[:98] + "..."
        res.append({
            "cid": obj.id,
            "author": author,
            "time": timestamp2str(obj.comment_time),
            "text": text,
            "email_hash": email_hash,
            "pid": obj.pid,
        })
    return res

def get_admin_post_list(x, y, post_type="", search=""):
    tmp = Post.objects.all()
    search_list = search.split()
    if post_type != "":
        tmp = tmp.filter(post_type=post_type)
    if len(search_list) > 0:
        title_set = tmp.all()
        text_set = tmp.all()
        for s in search_list:
            title_set = title_set.filter(title__icontains = s)
            text_set = text_set.filter(text__icontains = s)
        tmp = title_set | text_set
    tmp = tmp.order_by("-post_time")
    x = max(min(x, tmp.count()), 0)
    y = max(min(y, tmp.count()), 0)
    res = []
    while x < y:
        obj = tmp[x]
        x += 1
        res.append({
            "pid": obj.id,
            "title": obj.title,
            "type": obj.post_type,
            "time": obj.post_time,
            "protected": obj.protected,
        })
    return (tmp.count(), res)

def get_admin_comment_list(x, y, search=""):
    tmp = Comment.objects.all()
    search_list = search.split()
    if len(search_list) > 0:
        text_set = tmp.all()
        author_set = tmp.all()
        for s in search_list:
            text_set = text_set.filter(text__icontains = s)
            author_set = author_set.filter(author__icontains = s)
        tmp = text_set | author_set
    tmp = tmp.order_by("-comment_time")
    x = max(min(x, tmp.count()), 0)
    y = max(min(y, tmp.count()), 0)
    res = []
    username = get_option("username")
    user_email_hash = get_email_hash(get_option("email"))
    while x < y:
        obj = tmp[x]
        x += 1
        author = obj.author
        email_hash = None
        if obj.is_admin:
            author = username
            email_hash = user_email_hash
        else:
            email_hash = get_email_hash(obj.email)
        res.append({
            "cid": obj.id,
            "pid": obj.pid,
            "author": author,
            "text": obj.text,
            "time": obj.comment_time,
            "email_hash": email_hash,
        })
    return (tmp.count(), res)

def get_admin_pagination(num, page_size, post_list_len, key, GET={}, sub=""):
    page_cnt = post_list_len
    if page_cnt % page_size > 0:
        page_cnt = page_cnt // page_size + 1
    else:
        page_cnt = page_cnt // page_size
    if page_cnt <= 1:
        return []
    get = GET.copy()
    res = [(str(num) + " / " + str(page_cnt), "", "", "div")]
    if num > 1:
        get[key] = str(num - 1)
        url = "/admin" + sub + "?" + urllib.parse.urlencode(get)
        res.insert(0, ("<", url, "", "a"))
        get[key] = "1"
        url = "/admin" + sub + "?" + urllib.parse.urlencode(get)
        res.insert(0, ("<<", url, "", "a"))
    else:
        res.insert(0, ("<", "", "disabled", "div"))
        res.insert(0, ("<<", "", "disabled", "div"))
    if num < page_cnt:
        get[key] = str(num + 1)
        url = "/admin" + sub + "?" + urllib.parse.urlencode(get)
        res.append((">", url, "", "a"))
        get[key] = str(page_cnt)
        url = "/admin" + sub + "?" + urllib.parse.urlencode(get)
        res.append((">>", url, "", "a"))
    else:
        res.append((">", "", "disabled", "div"))
        res.append((">>", "", "disabled", "div"))
    return res

def media_exist(mid):
    return Media.objects.filter(id=mid).count() != 0

def save_media(file):
    name = file.name
    upload_time = int(time.time())
    md5 = hashlib.md5(str(upload_time).encode('utf-8'))
    md5.update(name.encode('utf-8'))
    path = md5.hexdigest() + os.path.splitext(name)[1]
    f = open(os.path.join(settings.BASE_DIR, "media", path), "wb")
    for chunk in file.chunks():
        f.write(chunk)
    f.close()
    Media(
        name = name,
        upload_time = upload_time,
        path = path,
    ).save()

def delete_media(mid):
    obj = Media.objects.get(id = mid)
    os.remove(os.path.join(settings.BASE_DIR, "media", obj.path))
    obj.delete()

def get_media_list(x, y, search=""):
    tmp = Media.objects.all()
    search_list = search.split()
    for s in search_list:
        tmp = tmp.filter(name__icontains = s)
    tmp = tmp.order_by("-upload_time")
    x = max(min(x, tmp.count()), 0)
    y = max(min(y, tmp.count()), 0)
    res = []
    while x < y:
        obj = tmp[x]
        x += 1
        res.append({
            "mid": obj.id,
            "name": obj.name,
            "path": obj.path,
            "time": timestamp2str(obj.upload_time),
        })
    return (tmp.count(), res)

def hcaptcha_verify(request, hcaptcha):
    secret = hcaptcha.get("secret", "")
    token = request.POST.get("h-captcha-response", "")
    sitekey = hcaptcha.get("key", "")
    params = {
        "secret": secret,
        "response": token,
        "sitekey": sitekey,
    }
    response = requests.post("https://hcaptcha.com/siteverify", params)
    content = json.loads(response.content)
    return content["success"]
