from django.shortcuts import render, redirect
from django.http import Http404
from django.contrib import messages
from django.core.exceptions import SuspiciousOperation
from . import installer, settings, auth, smtp
from .functions import get_option, set_option, get_navigation_links, \
        get_admin_navigation_links, save_post, get_post_data, \
        md2post, timestamp2str, get_post_list, get_abstract, \
        get_email_hash, get_comment_data, save_comment, \
        get_comments_with_pid, get_pagination, get_recent_comment_list, \
        post_exist, delete_post, comment_exist, get_admin_post_list, \
        get_admin_comment_list, get_admin_pagination, delete_comment, \
        get_site_icon, get_advanced_option, get_media_list, save_media, \
        media_exist, delete_media, hcaptcha_verify
import time, re, mimetypes

POST_NUM_PER_PAGE = 5
ADMIN_POST_PER_PAGE = 15
ADMIN_COMMENT_PER_PAGE = 10
ADMIN_MEDIA_PER_PAGE = 15
RECENT_LIST_SIZE = 10
ALLOWED_MEDIA_TYPE_PREFIX = (
    "video/",
    "image/",
    "audio/",
    "application/zip",
    "application/rar",
    "application/x-7z-compressed",
    "application/pdf"
)

def refresh_settings():
    global POST_NUM_PER_PAGE
    POST_NUM_PER_PAGE = get_advanced_option('post-number-per-page', 5)

refresh_settings()

def install_page(request):
    if settings.IS_INSTALLED:
        return redirect("/")
    if request.method == "POST":
        msgs = installer.check_input(request)
        if len(msgs) != 0:
            for msg in msgs:
                messages.error(request, msg)
            rep = redirect("/install")
            rep.set_cookie("site_name", request.POST.get("site-name", ""))
            rep.set_cookie("site_description", \
                    request.POST.get("site-description", ""))
            rep.set_cookie("username", request.POST.get("username", ""))
            rep.set_cookie("email", request.POST.get("email", ""))
            return rep
        installer.install(request)
        rep = redirect("/login")
        rep.delete_cookie("site_name")
        rep.delete_cookie("site_description")
        rep.delete_cookie("username")
        rep.delete_cookie("email")
        messages.success(request, "Installation is successful, please login.")
        return rep
    context = {
        "site_name": request.COOKIES.get("site_name", ""),
        "site_description": request.COOKIES.get("site_description", ""),
        "username": request.COOKIES.get("username", ""),
        "email": request.COOKIES.get("email", ""),
    }
    return render(request, 'install.html', context)

def login_page(request):
    if not settings.IS_INSTALLED:
        return redirect("/install")
    if request.session.get("logged_in", False):
        return redirect("/admin")
    hcaptcha = get_advanced_option("hcaptcha")
    if request.method == "POST":
        if hcaptcha != None:
            if not hcaptcha_verify(request, hcaptcha):
                messages.error(request, "Please complete the captcha.")
                rep = redirect("/login")
                rep.set_cookie("user", user)
                return rep
            user = request.POST.get("user", "")
            pswd = request.POST.get("password", "")
        if not auth.auth_user(user, pswd):
            messages.error(request, "Incorrect username / email or password.")
            rep = redirect("/login")
            rep.set_cookie("user", user)
            return rep
        request.session["logged_in"] = True
        rep = redirect("/admin")
        rep.delete_cookie("user")
        return rep
    context = {
        "user": request.COOKIES.get("user", ""),
        "icon_url": get_site_icon(),
        "site_name": get_option("site_name"),
        "hcaptcha": hcaptcha != None,
    }
    if context["hcaptcha"]:
        context["hcaptcha_key"] = hcaptcha.get("key", "")
    return render(request, 'login.html', context)

def logout_page(request):
    if not settings.IS_INSTALLED:
        return redirect("/install")
    if not request.session.get("logged_in", False):
        return redirect("/")
    request.session["logged_in"] = False
    request.session.flush()
    return redirect("/")

def index_page(request, num = 1):
    if not settings.IS_INSTALLED:
        return redirect("/install")
    logged_in = request.session.get("logged_in", False)
    search = request.GET.get("s", "")
    num = int(num)
    post_list = get_post_list(
            (num - 1) * POST_NUM_PER_PAGE,
            num * POST_NUM_PER_PAGE,
            check_top = True,
            logged_in = logged_in,
            session = request.session,
            search = search,
        )
    post_cnt = post_list[0]
    post_list = post_list[1]
    if num != 1 and len(post_list) == 0:
        raise Http404("Page does not exist")
    for post in post_list:
        post["time"] = timestamp2str(post["time"])
        post["text"] = get_abstract(md2post(post["text"]))
    get_urlencode = ""
    if request.GET.urlencode() != "":
        get_urlencode = '?' + request.GET.urlencode()
    context = {
        "logged_in": logged_in,
        "icon_url": get_site_icon(),
        "site_name": get_option("site_name"),
        "site_description": get_option("site_description"),
        "username": get_option("username"),
        "page_links": get_navigation_links(),
        "post_list": post_list,
        "recent_post_list": get_post_list(0, RECENT_LIST_SIZE)[1],
        "recent_comment_list": get_recent_comment_list(RECENT_LIST_SIZE),
        "pagination": get_pagination(
                num = num,
                page_size = POST_NUM_PER_PAGE,
                post_list_len = post_cnt,
                get_str = get_urlencode
            ),
        "user_avatar": "https://www.gravatar.com/avatar/" + \
                get_email_hash(get_option("email")) + "?s=300",
        "search_value": search,
    }
    return render(request, 'index.html', context)

def archives_page(request, pid):
    if not settings.IS_INSTALLED:
        return redirect("/install")
    if not post_exist(pid):
        raise Http404("Page does not exist")
    data = get_post_data(pid)
    logged_in = request.session.get("logged_in", False)
    pid = int(pid)
    if not logged_in and data["type"] == "draft":
        raise Http404("Page does not exist")
    hcaptcha = get_advanced_option("hcaptcha")
    if request.method == "POST":
        page_url = request.build_absolute_uri("/archives/" + str(pid))
        if not logged_in and hcaptcha != None:
            if not hcaptcha_verify(request, hcaptcha):
                messages.error(request, "Please complete the captcha.")
                return redirect(page_url + "#reply-form")
        if request.POST.get("is-password-form", "0") == "1":
            password = request.POST.get("post-password", None)
            if password != data["password"]:
                messages.error(request, "The password is incorrect.")
                return redirect(page_url)
            request.session["post_pswd_of_" + str(pid)] = password
            return redirect(page_url)
        if data["type"] == "draft" or not data["allow_comment"]:
            raise SuspiciousOperation("Invalid comment")
        parent = request.POST.get("comment-parent", "0")
        if not parent.isdigit():
            messages.error(request, "Invalid parent comment id")
            return redirect(page_url + "#reply-form")
        parent = int(parent)
        if parent != 0:
            if comment_exist(parent):
                data = get_comment_data(parent)
            else:
                data = {
                    "pid": 0,
                    "status": "pending",
                }
            if data["pid"] != pid or data["status"] != "published":
                messages.error(request, "Invalid parent comment id")
                return redirect(page_url + "#reply-form")
        if request.POST.get("comment-logged-in", "0") == "1":
            if not logged_in:
                messages.error(
                    request,
                    "The session has timed out, please log in again"
                )
                return redirect(page_url + "#reply-form")
            content = request.POST.get("comment-content", "")
            if content == "":
                messages.error(request, "Comment content cannot be empty")
                return redirect(page_url + "#reply-form")
            cid = save_comment(
                cid = 0,
                data = {
                    "author": "",
                    "email": "",
                    "is_admin": True,
                    "url": "",
                    "text": content,
                    "pid": pid,
                    "parent": parent,
                    "status": "published",
                    "time": int(time.time()),
                }
            )
            comment_url = page_url + "#comment-" + str(cid)
            if parent != 0 and smtp.send_when_reply():
                data = get_comment_data(parent)
                if not data["is_admin"]:
                    smtp.send_reply_notification(
                        data["author"],
                        data["email"],
                        comment_url
                    )
            return redirect(comment_url)
        author = request.POST.get("comment-name", "").strip()
        email = request.POST.get("comment-email", "").strip()
        url = request.POST.get("comment-url", "").strip()
        content = request.POST.get("comment-content", "")
        flag = False
        if author.lower() == get_option("username").lower():
            messages.error(
                request,
                "You should not use the administrator's name."
            )
            flag = True
        elif author == "":
            messages.error(request, "Name cannot be empty")
            flag = True
        elif len(author) > 200:
            messages.error(request, "Name is too long")
            flag = True
        if email.lower() == get_option("email").lower():
            messages.error(
                request,
                "You should not use the administrator's email."
            )
            flag = True
        elif not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email):
            messages.error(request, "Invalid email address")
            flag = True
        if len(url) > 255:
            messages.error(request, "Website URL is too long")
            flag = True
        elif len(url) != 0 and \
                not (url.startswith("http://") or url.startswith("https://")):
            messages.error(
                request,
                "Invalid Website URL (it should start with https:// or http://)"
            )
            flag = True
        if content == "":
            messages.error(request, "Comment content cannot be empty")
            flag = True
        comment_re = get_advanced_option("comment-re")
        if comment_re != None:
            for r in comment_re:
                if re.search(r, content, re.IGNORECASE) != None:
                    messages.error(
                        request,
                        "Comment content containing prohibited words"
                    )
                    flag = True
                    break
        if flag:
            return redirect(page_url + "#reply-form")
        cid = save_comment(
            cid = 0,
            data = {
                "author": author,
                "email": email,
                "is_admin": False,
                "url": url,
                "text": content,
                "pid": pid,
                "parent": parent,
                "status": "published",
                "time": int(time.time()),
            }
        )
        comment_url = page_url + "#comment-" + str(cid)
        if parent == 0:
            if smtp.send_when_comment():
                smtp.send_comment_notification(data["title"], comment_url)
        else:
            if smtp.send_when_reply():
                data = get_comment_data(parent)
                smtp.send_reply_notification(
                    data["author"],
                    data["email"],
                    comment_url
                )
        return redirect(comment_url)
    if data["protected"] and not logged_in:
        if request.session.get("post_pswd_of_" + str(pid), None) \
                != data["password"]:
            context = {
                "visible": False,
                "logged_in": logged_in,
                "icon_url": get_site_icon(),
                "site_name": get_option("site_name"),
                "page_links": get_navigation_links(),
                "post_title": data["title"],
                "post_comments_num": 0,
                "post_time": timestamp2str(data["time"]),
                "recent_post_list": get_post_list(0, RECENT_LIST_SIZE)[1],
                "recent_comment_list": \
                        get_recent_comment_list(RECENT_LIST_SIZE),
                "hcaptcha": hcaptcha != None,
            }
            if context["hcaptcha"]:
                context["hcaptcha_key"] = hcaptcha.get("key", "")
            return render(request, 'archives.html', context)
    post = md2post(data["text"])
    context = {
        "visible": True,
        "logged_in": logged_in,
        "icon_url": get_site_icon(),
        "username": get_option("username"),
        "site_name": get_option("site_name"),
        "page_links": get_navigation_links(),
        "post_pid": pid,
        "post_type": data["type"],
        "post_title": data["title"],
        "post_content": post,
        "post_comments_num": data["comments_num"],
        "post_time": timestamp2str(data["time"]),
        "post_allow_comment": data["allow_comment"],
        "recent_post_list": get_post_list(0, RECENT_LIST_SIZE)[1],
        "recent_comment_list": get_recent_comment_list(RECENT_LIST_SIZE),
        "hcaptcha": hcaptcha != None,
    }
    if context["hcaptcha"]:
        context["hcaptcha_key"] = hcaptcha.get("key", "")
    if data["allow_comment"] and data["type"] != "draft":
        context["comments"] = get_comments_with_pid(pid)
    return render(request, 'archives.html', context)

def edit_page(request, pid = 0):
    if not settings.IS_INSTALLED:
        return redirect("/install")
    if not request.session.get("logged_in", False):
        return redirect("/login")
    pid = int(pid)
    if pid != 0 and not post_exist(pid):
        raise Http404("Page does not exist")
    if request.method == "POST":
        post_time = request.POST.get("post-time", "")
        if post_time == "" or not post_time.isdigit():
            post_time = time.time()
        post_time = int(post_time)
        title = request.POST.get("post-title", "")
        if title == "":
            title = "New post"
        post_type = request.POST.get("post-type", "post")
        if not post_type in ("post", "page", "draft"):
            post_type = post
        save_post(
            pid = pid,
            data = {
                "title": title,
                "text": request.POST.get("post-content", ""),
                "type": request.POST.get("post-type", "post"),
                "protected": request.POST.get("protected", "") == "on",
                "password": request.POST.get("password", ""),
                "top": request.POST.get("top", "") == "on",
                "allow_comment": request.POST.get("allow-comment", "") == "on",
                "time": post_time,
            }
        )
        messages.success(request, "Article saved successfully.")
        return redirect("/admin")
    if request.GET.get("action", "") == "delete":
        delete_post(pid)
        messages.success(request, "Article deleted successfully.")
        return redirect("/admin")
    context = {
        "pid": 0,
        "page_title": "Create a new article",
        "icon_url": get_site_icon(),
        "site_name": get_option("site_name"),
        "page_links": get_admin_navigation_links(),
        "post_type": "post",
        "post_title": "",
        "post_content": "",
        "post_protected": False,
        "post_password": "",
        "post_allow_comment": True,
        "post_top": False,
        "post_time": "",
    }
    if pid > 0:
        data = get_post_data(pid)
        context["pid"] = pid
        context["page_title"] = "Editing " + data["title"]
        context["post_type"] = data["type"]
        context["post_title"] = data["title"]
        context["post_content"] = data["text"]
        context["post_protected"] = data["protected"]
        context["post_password"] = data["password"]
        context["post_allow_comment"] = data["allow_comment"]
        context["post_top"] = data["top"]
        context["post_time"] = str(data["time"])
    return render(request, 'edit.html', context)

def edit_comment_page(request, cid = 0):
    if not settings.IS_INSTALLED:
        return redirect("/install")
    if not request.session.get("logged_in", False):
        return redirect("/login")
    cid = int(cid)
    if cid == 0 or (not comment_exist(cid)):
        raise Http404("Page does not exist")
    data = get_comment_data(cid)
    if request.method == "POST":
        comment_time = request.POST.get("comment-time", "")
        if comment_time == "" or not comment_time.isdigit():
            comment_time = time.time()
        comment_time = int(comment_time)
        data["time"] = comment_time
        comment_text = request.POST.get("comment-content", "")
        if comment_text != "":
            data["text"] = comment_text
        comment_status = request.POST.get("comment-status", "published")
        if comment_status in ("published", "pending"):
            data["status"] = comment_status
        if not data["is_admin"]:
            comment_author = request.POST.get("comment-author", "")
            if comment_author != "":
                data["author"] = comment_author
            comment_email = request.POST.get("comment-email", "")
            if comment_email != "":
                data["email"] = comment_email
            data["url"] = request.POST.get("comment-url", "")
        save_comment(cid, data)
        messages.success(request, "Comment saved successfully.")
        return redirect("/admin")
    if request.GET.get("action", "") == "delete":
        delete_comment(cid)
        messages.success(request, "Comment deleted successfully.")
        return redirect("/admin")
    context = {
        "cid": cid,
        "page_title": "Editing " + data["author"] + "'s comment",
        "icon_url": get_site_icon(),
        "site_name": get_option("site_name"),
        "page_links": get_admin_navigation_links(),
        "comment_author": data["author"],
        "comment_email": data["email"],
        "comment_content": data["text"],
        "comment_pid": data["pid"],
        "comment_time": data["time"],
        "comment_status": data["status"],
        "comment_url": data["url"],
        "comment_is_admin": data["is_admin"],
    }
    return render(request, 'edit_comment.html', context)

def admin_page(request):
    if not settings.IS_INSTALLED:
        return redirect("/install")
    if not request.session.get("logged_in", False):
        return redirect("/login")
    post_page = request.GET.get("post-page", "1")
    if not post_page.isdigit():
        raise Http404("Page does not exist")
    post_page = int(post_page)
    comment_page = request.GET.get("comment-page", "1")
    if not comment_page.isdigit():
        raise Http404("Page does not exist")
    comment_page = int(comment_page)
    post_type = request.GET.get("post-type", "")
    post_search = request.GET.get("post-search", "")
    comment_search = request.GET.get("comment-search", "")
    if not post_type in ("all", "post", "page", "draft"):
        post_type = "all"
    post_list = get_admin_post_list(
            (post_page - 1) * ADMIN_POST_PER_PAGE,
            post_page * ADMIN_POST_PER_PAGE,
            post_type = post_type.replace("all", ""),
            search = post_search,
        )
    post_cnt = post_list[0]
    post_list = post_list[1]
    comment_list = get_admin_comment_list(
            (comment_page - 1) * ADMIN_COMMENT_PER_PAGE,
            comment_page * ADMIN_COMMENT_PER_PAGE,
            search = comment_search,
        )
    comment_cnt = comment_list[0]
    comment_list = comment_list[1]
    if (len(post_list) == 0 and post_page != 1) or \
            (len(comment_list) == 0 and comment_page != 1):
        raise Http404("Page does not exist")
    for i in post_list:
        i["type"] = i["type"].capitalize()
        i["time"] = timestamp2str(i["time"])
    for i in comment_list:
        i["time"] = timestamp2str(i["time"])
    context = {
        "site_name": get_option("site_name"),
        "icon_url": get_site_icon(),
        "page_links": get_admin_navigation_links(),
        "post_cnt": post_cnt,
        "post_list": post_list,
        "comment_cnt": comment_cnt,
        "comment_list": comment_list,
        "post_pagination": get_admin_pagination(
                num = post_page,
                page_size = ADMIN_POST_PER_PAGE,
                post_list_len = post_cnt,
                key = "post-page",
                GET = request.GET,
            ),
        "comment_pagination": get_admin_pagination(
                num = comment_page,
                page_size = ADMIN_COMMENT_PER_PAGE,
                post_list_len = comment_cnt,
                key = "comment-page",
                GET = request.GET,
            ),
        "post_type": post_type,
        "post_search": post_search,
        "comment_search": comment_search,
    }
    return render(request, 'admin.html', context)

def settings_page(request):
    if not settings.IS_INSTALLED:
        return redirect("/install")
    if not request.session.get("logged_in", False):
        return redirect("/login")
    if request.method == "POST":
        site_name = request.POST.get("site-name", "")
        site_description = request.POST.get("site-description", "")
        advanced_settings = request.POST.get("advanced-settings", "")
        username = request.POST.get("username", "")
        email = request.POST.get("email", "")
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm-password", "")
        flag = False
        if site_name != "":
            set_option("site_name", site_name)
        else:
            messages.error(request, "Site name cannot be empty.")
            flag = True
        set_option("site_description", site_description)
        set_option("advanced_settings", advanced_settings)
        if username != "":
            set_option("username", username)
        else:
            messages.error(request, "Username cannot be empty.")
            flag = True
        if re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email):
            set_option("email", email)
        else:
            messages.error(request, "The e-mail format is incorrect.")
            flag = True
        if password != "":
            if len(password) < 6:
                messages.error(
                        request,
                        "The password length is at least 6 digits."
                    )
                flag = True
            elif len(password) > 32:
                messages.error(
                        request,
                        "The password length is at most 32 digits."
                    )
                flag = True
            elif password != confirm_password:
                messages.error(
                        request,
                        "The two passwords entered are different."
                    )
                flag = True
            else:
                set_option("password", auth.password_hash(password))
        if flag:
            messages.warning(request, "Only correct inputs are saved.")
        else:
            messages.success(request, "Settings saved successfully.")
        refresh_settings()
        return redirect("/admin/settings")
    context = {
        "site_name": get_option("site_name"),
        "icon_url": get_site_icon(),
        "page_links": get_admin_navigation_links(),
        "site_description": get_option("site_description"),
        "advanced_settings": get_option("advanced_settings"),
        "username": get_option("username"),
        "email": get_option("email"),
    }
    return render(request, 'settings.html', context)

def media_page(request):
    if not settings.IS_INSTALLED:
        return redirect("/install")
    if not request.session.get("logged_in", False):
        return redirect("/login")
    if request.method == "POST":
        file = request.FILES.get("new-file", None)
        if file == None:
            raise SuspiciousOperation("Invalid file")
        file_type = str(mimetypes.guess_type(file.name)[0])
        for prefix in ALLOWED_MEDIA_TYPE_PREFIX:
            if file_type.startswith(prefix):
                save_media(file)
                messages.success(request, "The file was uploaded successfully.")
                return redirect("/admin/media")
        messages.error(request, "Unsupported file type.")
        return redirect("/admin/media")
    if request.GET.get("action", "") == "delete":
        mid = int(request.GET.get("mid", "0"))
        if not media_exist(mid):
            raise Http404("File does not exist")
        delete_media(mid)
        messages.success(request, "The file was deleted successfully.")
        return redirect("/admin/media")
    page = request.GET.get("page", "1")
    search = request.GET.get("search", "")
    if not page.isdigit():
        raise Http404("Page does not exist")
    page = int(page)
    media_list = get_media_list(
        (page - 1) * ADMIN_MEDIA_PER_PAGE,
        page * ADMIN_MEDIA_PER_PAGE,
        search,
    )
    media_cnt = media_list[0]
    media_list = media_list[1]
    context = {
        "site_name": get_option("site_name"),
        "icon_url": get_site_icon(),
        "page_links": get_admin_navigation_links(),
        "search": search,
        "media_list": media_list,
        "pagination": get_admin_pagination(
                num = page,
                page_size = ADMIN_MEDIA_PER_PAGE,
                post_list_len = media_cnt,
                key = "page",
                GET = request.GET,
                sub = "/media"
            ),
    }
    return render(request, 'media.html', context)
