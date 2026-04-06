
from https://ssb22.user.srcf.net/adjuster/twitter.html (also [mirrored on GitLab Pages](https://ssb22.gitlab.io/adjuster/twitter.html) just in case)

# Twitter on a 1982 BBC Micro

The Twitter platform has become socially worse since I posted this. I’m leaving it up for historical interest only and **not** as a recommendation of Twitter.

![twitter.jpg](https://ssb22.user.srcf.net/adjuster/twitter.jpg) In 2015 the National Museum of Computing at Bletchley Park displayed photographs of some of their classroom activities using 1980s BBC Microcomputers. In one picture, a child had typed the word `TWITTER` at the 1982 BBC BASIC prompt, perhaps thinking that this would somehow take them to the social networking website called Twitter. (Website? What’s that in 1982?) BBC BASIC had just said `Mistake` because it wasn’t a well-formed command (the word `TWITTER` would work as a variable name, but in BBC BASIC you have to specify what to *do* with that variable—even if it were already defined, you’d still need to `PRINT` it or something; you can’t just inspect variables by typing their names alone as you can in Python).

The organisers evidently thought the child’s attempt to load Twitter to be cute enough to post a photograph of the error message with the caption “Some things the Beeb won’t do.”

I must say: did you want something like *this*?

![twitter.png](https://ssb22.user.srcf.net/adjuster/twitter.png) ![tscreen.png](https://ssb22.user.srcf.net/adjuster/tscreen.png)

Admittedly, this (emulated) Beeb had some extra help in the form of an RS423 connection to a Debian GNU/Linux 8 “Jessie” system (running `edbrowse` in the 1<sup>st</sup> screenshot, and PhantomJS with [pbmtobbc](https://ssb22.user.srcf.net/adjuster/pbmtobbc.py) in the 2<sup>nd</sup> screenshot). But then, some mobile phones use browsers that require a transcoding proxy between the phone and the website, and few people say the phone “won’t do” the website just because it’s not doing *all* the processing by itself. (They might say it’s not doing the site *very well*, but that’s not the same question as whether it will do it at all.)

While we understand the caption’s intended meaning, in all fairness we should point out that the Beeb at the museum wouldn’t do Twitter because it wasn’t connected to a suitable server over RS423 (or over Econet via BeebFrame), not just because it was a Beeb.

## Technical details

The one-liner to type on the BBC Micro is as follows:

`MO.6:OS."FX2,2":REP.IFAD.-1:OS."FX3,1":V.GET:OS."FX3,0":U.0:EL.:IFAD.-2:OS."FX2,1":V.GET:OS."FX2,2":U.0:EL.:U.0`

(I said Mode 6 so that “[” and “]” display as square brackets; they’d be arrows in Mode 7. Those with good monitors and eyesight might like to try the 80-column Mode 3 instead, and `pbmtobbc` works best in Mode 4.)

On the server side, it’s necessary to add a rate-throttling script to reduce buffer overflows, plus translate carriage returns etc. Something like the example script below.

If `edbrowse` is not available in your distro, you could also try `w3c-libwww-apps` to get the 1992 CERN line-mode browser as `www`, which is what I’ve assumed in this example script and is arguably easier for beginners. This will however need [Web Adjuster](../README.md) to do its Javascript, SSL and Unicode rendering (none of which were around in 1992)—run `adjuster.py` with (e.g.) `--js_interpreter=PhantomJS --address=127.0.0.1 --default_site=twitter.com.0 --host_suffix=localhost --wildcard_dns=False --open_proxy --htmlFilter="iconv -c -f UTF8 -t ASCII//TRANSLIT"` and then tell `www` to `goto http://localhost:28080/` (that `iconv` command transliterates simple Unicode punctuation into ASCII, but won’t help much if you want to view a non-Latin language).

If you want to run a *screen mode* browser like `lynx` (with cursor positioning, not just line-mode interaction), some versions of Kermit can emulate the VT-52 “DECscope”, or the Master’s `*TERMINAL` (press Enter at the `=` prompt) has ANSI (VT100). Cambridge University used BBC Micros as terminals to its IBM mainframe called “Phoenix” which was retired in 1995 (2 years before I started as an undergraduate)—I’m told they were Model Bs with custom terminal ROMs and matching `termcap` files on the Unix side, but I don’t know what they were capable of.

The BBC’s entire graphics repertoire can be driven with `VDU` codes sent over the link:![vdu25.png](https://ssb22.user.srcf.net/adjuster/vdu25.png) here I’ve kludged my [old music program](https://ssb22.user.srcf.net/mwrhome/)’s plotter output into BBC `PLOT` codes (`VDU 25`) in Mode 0, but monochrome images *are* better transferred as bitmaps split into 8x8 blocks for `VDU 23` (see `pbmtobbc` above). The early Phoenix BCPL version of PMS had a BBC-terminal preview mode which used 8x8 characters in some way but didn’t attempt to render curves.

Below is a simple script for rate-throttling and linefeed translation to go with the above `FX` one-liner. This script is for GNU/Linux; on the Mac you’ll have to do without `pty` so you might be more limited in the commands you can run. I’ve also assumed the BBC emulator is running its RS423 connection in Server mode (which tends to be more reliable than Client mode) and is listening on `localhost` port 2323.
```

#!/usr/bin/env python2
import os,fcntl,time,sys
toNC,fromNC = os.popen4("nc localhost 2323")
os.system("rm -f /tmp/w3c-cache/.lock")
toWWW,fromWWW = os.popen4("python2 -c 'import pty,time
pty.spawn(\"www\")
time.sleep(1000000)'")
fcntl.fcntl(fromWWW, fcntl.F_SETFL,os.O_NONBLOCK)
fcntl.fcntl(fromNC, fcntl.F_SETFL,os.O_NONBLOCK)
while True:
    try: typed = fromNC.read(1024).replace("\r","\n")
    except IOError: typed = ""
    if typed:
        toWWW.write(typed),toWWW.flush()
        sys.stdout.write(typed),sys.stdout.flush()
    try: out = fromWWW.read(1024)
    except IOError: out = ""
    if out:
        sys.stdout.write(out),sys.stdout.flush()
    out = out.split("\n")
    for l in out[:-1]:
        toNC.write(l+"\r\n"), toNC.flush()
        time.sleep(0.5)
    out = out[-1]
    if out: toNC.write(out), toNC.flush()
    time.sleep(0.5)
```
## But can you log in?

That child might still be disappointed to find they can’t actually *log in* to Twitter, because the login process depends on interacting with graphics. An RS423-based VNC viewer would be theoretically possible (it would have to reduce the colour depth from 8 to 3, 2 or 1, and the mouse emulation could be tricky) but it would be *slow*. It might have been possible to use `curl` commands with an API key (but the rules about this repeatedly changed in 2023), or they could post on another platform such as `public_html` which I can update from any command-line terminal (although I wouldn’t go as far as doing it from a Beeb—besides anything else, some years after I stopped using BBCs I switched to the Dvorak keyboard layout, so in order to work on a BBC terminal comfortably I’d now have to write a remapper for it).

## Programming the BBC instead

Of course you could always do what we used to do and just program the BBC. Immediate-mode “one-liners”, being limited to 238 keystrokes, are relatively quick to type in; here’s some I made earlier:
* Bat-and-ball game (use keys `Z` and `X` to play): `REP.MO.2:DR.0,980:DR.1279,980:DR.1279,0:X=8:Y=8:H=8:V=4:B=0:REP.H=H*SGN(.5-POINT(X+H,Y)):V=V*SGN(.5-POINT(X,Y+V)):PL.71,X,Y:X=X+H:Y=Y+V:GC.0,3:PL.69,X,Y:MOVEB,0:PL.3,50,0:B=B+9*(INKEY-98-INKEY-67):GC.0,6:MOVEB,0:PL.1,50,0:U.Y<0:V.7:U.0`
* Ski-slope game (it stops if you win): `MO.1:REP.S=RND(-1)*0:N=9:P=17:V.30,16,23,1;:REP.N=N+SGNRND:N=N-(N<0)+(N>22):P=P-(P>0)*INKEY-98+(P<38)*INKEY-67:C.1:P.TAB(N,31)"*:"TAB(16-S/200)":*":C.2:V.31,P,0,86,31,0,29:S=S+1:C.3:P.LE.STR.S,-9*(S MOD100=0)):U.PO.P*32+16,980):U.S=2631`
* ![../css/eulerian.png](https://ssb22.user.srcf.net/css/eulerian.png)Draw [Eulerian paths](https://ssb22.user.srcf.net/css/eulerian.html) around 13 different polygons: `MO.2:R=450:F.N=3TO15:E=2*PI/N:M=N MOD2:T=N*(N-M)/2-(N-1)*(1-M):CLS:P.N,T:S=0:F.U=1TOT:Q=1:REP.M=-Q*(PO.8*S,4*Q)=0):Q=Q+1:U.M:GC.0,M:PL.69,8*S,4*M:D=S*E:MOVER+R*COSD,R+R*SIND:S=(S+M)MODN:D=S*E:DR.R+R*COSD,R+R*SIND:N.:I."PRESS RETURN:"A:N.`
* Mandelbrot plot (this one takes about 20 minutes—not the *fastest* M-set, but probably the best we can do in a one-liner): `MO.2:OS."FX10,0":F.X%=0TO992S.8:I=X%/331-2:F.Y%=0TO500S.4:J=Y%/333:K=0:L=0:Q=I-.25:Q=Q*Q+J*J:T%=-15*(Q*(Q+(I-.25))<.25*J*J):REP.W=I+K*K-L*L:L=J+2*K*L:K=W:T%=T%+1:U.K*K+L*L>4ORT%=16:GC.0,T%:PL.69,144+X%,500-Y%:PL.69,144+X%,500+Y%:N.:N.`
* Colour-coded tesseract: `MO.1:CL.:DIMC(3):F.W=0TO15:GC.0,1:F.L=0TO3:F.P=4TO5:F.M=0TO3:C(M)=SGN(2^M A.W)*(P=4ORL<>M)*2+1:N.:F.H=2TO3:X=C(1)/2+C(H)*.87:C(H)=C(1)*.87-C(H)/2:C(1)=X:N.:Q=C(0)+5:Q=3200/(C(1)*2/Q+3)/Q:PL.P,C(2)*Q+640,C(3)*Q+512:N.:GC.0,2+(W A.1):N.:N.`

  Extending to 5 dimensions:

   You can extend this to a 5-cube by changing the first three or four instances of `3` to `4`, changing `15` to `31` and `(2)` to `(4)`, and ideally changing the `MODE` to 2 and the `A.1` to `A.3` for better colour coding. Our `Q` perspective calculation would then operate on the 4<sup>th</sup> and 5<sup>th</sup> dimensions but ignore the 3<sup>rd</sup>, so it won’t be as clear.

* Braille alphabet chart (fits in a ‘tweet’ of the original 140-character type, with room to spare): `MO.7:A=&404:$A="!%`£`+)'/-&.153;97?=6>quns{y":F.L=0TO25:V.10*-(L MOD8=0),145+L MOD7,154,65+L,9,A?L:N.:P.`
* Simple colour scrolling (this is what convinced certain other children at primary school that I wasn’t a ‘thicko’—having planned a larger program I was surprised they were impressed by a mere 27 keystrokes): `MO.2:REP.:C.RND(135):P.:U.0`
* Well you can do it in 24 starting at the Mode 7 prompt: `REP.V.128+RND(7),157:U.0`
* Version with numbers too: `MO.2:C.0:REP.C.RND(7)+128:P.RND;:U.0`
* Or just have random triangles: `MO.2:REP.GC.0,RND(7):PL.85,RND(1280),RND(1024):U.0`

   (if you’re on a Master, try changing that `85` to `205` for ellipses)

For the sanity of museum personnel, I’ll refrain from posting a noise demonstration here.

The Cambridge Centre for Computing History has a BBC whose `F` key is broken. If you’re on that one and don’t fancy rewriting code to avoid the letter F, try `OS."K.0"+CHR.70` to program function key *f0* to `F`. Or use my horrible hack `!2832=17937` to program all 10 function keys to `F` (works only on an unexpanded Model B with no `*KEY` before or after).

Copyright and Trademarks:
All material © Silas S. Brown unless otherwise stated.
Debian is a trademark owned by Software in the Public Interest, Inc.
Javascript is a trademark of Oracle Corporation in the US.
Linux is the registered trademark of Linus Torvalds in the U.S. and other countries.
Mac is a trademark of Apple Inc.
Python is a trademark of the Python Software Foundation.
Twitter and Tweet are trademarks of X Inc (previously Twitter Inc).
Unicode is a registered trademark of Unicode, Inc. in the United States and other countries.
Unix is a trademark of The Open Group.
VNC is a registered trademark of RealVNC Limited.
Any other [trademarks](https://ssb22.user.srcf.net/trademarks.html) I mentioned without realising are trademarks of their respective holders.
