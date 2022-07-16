import os, re, time
from . import settings
from .auth import password_hash
from .functions import set_option, save_post, save_comment

FIRST_POST_TITLE = r"Hello World!"

FIRST_POST_TEXT = \
r'''## Congratulations!

You made it! Welcome to the December blogging system!

This is the first article in the site. You can always delete it and start your writing journey!

## Some Useful Tips

### Markdown & LaTeX & Code Highlighting

The December system support Markdown & LaTeX & Code Highlighting **natively**, so you don't need to install extra plugins. This is actually pretty cool.

You can go to the editing page of this article to see its Markdown source code.

Or you can go to [this place](https://www.markdownguide.org/basic-syntax/) to learn more about Markdown syntax.

A simple example of LaTeX:

$$e^{ \pm i\theta } = \cos \theta \pm i\sin \theta$$

(Of course you are able to use the inline math mode: $e^{ \pm i\theta } = \cos \theta \pm i\sin \theta$!)

And for code highlighting, you can do:

```python
print("Hello World!")
```

### Abstract Divider

Use `<!--more-->` as abstract divider. When displayed on the home page, the content behind the abstract divider is hidden.

<!--more-->

*This will not be displayed on the home page.*

### Avatar

The December system is using [Gravatar](http://gravatar.com/emails/) as its avatar source.

### Other Problems

If you have any additional questions, please check out the [Github page](https://github.com/trinitrotofu/December) of the December blogging system.

## The End

Happy with your writing journey!'''

FIRST_COMMENT_TEXT = \
r'''This is the first comment in your site.
Feel free to delete it, and start having some fun!'''

def check_input(request):
    res = []
    data = request.POST
    if data["site-name"] == "":
        res.append("Site name cannot be empty.")
    if data["username"] == "":
        res.append("Username cannot be empty.")
    if len(data["password"]) < 6:
        res.append("The password length is at least 6 digits.")
    elif len(data["password"]) > 32:
        res.append("The password length is at most 32 digits.")
    if data["password"] != data["confirm-password"]:
        res.append("The two passwords entered are different.")
    if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", data["email"]):
        res.append("The e-mail format is incorrect.")
    return res

def install(request):
    data = request.POST
    set_option("site_name", data["site-name"])
    set_option("site_description", data["site-description"])
    set_option("username", data["username"])
    set_option("password", password_hash(data["password"]))
    set_option("email", data["email"])
    set_option("advanced_settings", "{}")
    config_path = os.path.join(
            settings.BASE_DIR,
            'configs',
            'is_installed'
        )
    open(config_path, "w").close()
    settings.IS_INSTALLED = True
    pid = save_post(
        pid = 0,
        data = {
            "title": FIRST_POST_TITLE,
            "text": FIRST_POST_TEXT,
            "type": "post",
            "protected": False,
            "password": "",
            "top": False,
            "allow_comment": True,
            "time": int(time.time()),
        }
    )
    save_comment(
        cid = 0,
        data = {
            "author": "",
            "email": "",
            "is_admin": True,
            "url": "",
            "text": FIRST_COMMENT_TEXT,
            "pid": pid,
            "parent": 0,
            "status": "published",
            "time": int(time.time()),
        }
    )
