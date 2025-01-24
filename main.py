from router.fs import fs
from router.kbqa import kbqa
from router.user import user
from router.screen import screen
from router.datahelper import dh
from util.encryption import mid_decryption

from sanic import Sanic

app = Sanic(__name__)
app.config.REQUEST_TIMEOUT = 9999999
app.config.RESPONSE_TIMEOUT = 9999999
# app.middleware(mid_decryption)
app.blueprint(dh)
app.blueprint(fs)
app.blueprint(user)
app.blueprint(kbqa)
app.blueprint(screen)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=33006, workers=3, auto_reload=False, debug=True)
