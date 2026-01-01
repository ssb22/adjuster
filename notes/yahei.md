
from https://ssb22.user.srcf.net/law/yahei.html (also [mirrored on GitLab Pages](https://ssb22.gitlab.io/law/yahei.html) just in case)

# Loophole in Microsoft YaHei font license?

Most free Chinese fonts are not well suited to being displayed at small pixel sizes on low-DPI devices. In general, you must choose between either:
* getting CJK-LaTeX to render Arphic PL fonts at low DPI, and substituting variants for any Chinese characters not in the original GB2312/Big5 set—this might be an awkward setup for your application;
* or putting up with bad placement of the strokes (causing, for example, end-of-sentence Chinese stops to appear lop-sided instead of circular, and baselines to be uneven),
* or use blurry anti-aliasing (if your output device or format even supports shading),
* or use a set of bitmap fonts (e.g. Wenquanyi Bitmap Song)—these display well at the specific pixel sizes they were designed for, but look bad at other sizes (and if you want to get a modern Web browser to do the rendering then you might find it refuses to load bitmap fonts and you have to use the `--render` options of [Web Adjuster](../README.md) or something).

Android users might think the Noto CJK font works well, but that’s only if your device has a high DPI and won’t carry over to an image file of limited size that also aims for compatibility with low-DPI devices.

The non-free font “Microsoft YaHei” commissioned for Windows Vista was extremely well “hinted” for use at many small pixel sizes (9px+) and is also completely scalable. Additionally it makes a reasonable font for the display of Pinyin—unlike the earlier “SimSun” font, it doesn’t display “a” as “ɑ” which pinyin’s inventor Zhou Youguang dismissed. And YaHei can also be used to render Chinese text in POV-Ray, unlike the Unicode TTF versions of Arphic and WenQuanYi which are not correctly parsed by POV-Ray as of version 3.7.

But is YaHei legal to use outside of Microsoft Windows?

The 1996 through 2002 versions of Microsoft’s Latin “Core fonts for the Web” came with license agreements that did not restrict which operating system you may use, as long as the downloads were provided as-is with nothing added (so tools to adapt them for other operating systems were provided separately). This practice was stopped in 2002, apparently because they didn’t like how widely these fonts were being used in non-Microsoft systems, and subsequent font releases (including the Chinese YaHei font) came with more restrictive licenses that tended to require all users to be on Windows.

From 2008 to 2018 Microsoft had a file called `VistaFont_CHS.EXE` on the Official Microsoft Download Center (spelled the American way) under the name “Simplified Chinese ClearType fonts for Windows XP” (the font was commissioned for Vista but backported to XP). The click-through EULA said you can “install and use any number of copies of the software on your devices running validly licensed copies of Microsoft Windows XP, Microsoft Windows Server 2003 and Microsoft Windows Vista” and “you may not copy, install or use the fonts on other devices.”

So you might think “OK, let’s boot Windows on my old dual-boot machine, install the font onto that validly-licensed copy of Windows, and then reboot into GNU/Linux on the same machine and set it to use the font files on the Windows partition”. But the EULA comes back with “You may use the fonts that accompany this software only to display and print content from a device **running** a Microsoft Windows operating system” (emphasis mine).

But there *might* be a loophole on this last point, because:
* The EULA is *first* presented in Chinese, and it *doesn’t* say the English version takes precedence in the event of disagreement, so it *might* be reasonable to claim that the Chinese version has priority by way of it being presented first—and note I say “Chinese version” not “Chinese translation” because how do *we* know which language was a translation?—for all we can tell from that self-contained “entire agreement” EULA, the Chinese might have been the *original* and the English might be the imperfect translation,
* and the Chinese version of that sentence is 您可以使用本软件附带的字体进行显示和打印，但显示和打印的内容必须来自运行Microsoft Windows操作系统的设备 which I understand as “you may use fonts included in this software to display and print, but *the content* being displayed and printed must have *originally* come from equipment running the Microsoft Windows operating system”. In other words, if you download Chinese text from a website or other source whose *creators* used Windows, then you may use the YaHei font to display it (or to create a screenshot, which Microsoft’s FAQ said they view as “printing”) even if *you* are not using Windows.
* And the Chinese version of “not use the fonts on other devices” comes at the end of the same Condition 4 that just said you *can* use them if you’re displaying content that originated on a Windows system (oh, and that you shouldn’t bypass any font-embedding restrictions set in the `.ttf` file—YaHei’s is set to Type 8 which allows embedding with editing but not permanent reinstallation—and that downloads to printers and other output devices must be temporary, but this sentence seems to act parenthetically and shouldn’t get in the way of the fact that the “other” in “no other devices” at the end of Condition 4 now means other than devices currently in use for displaying “content that originally came from a Windows system” at the start of Condition 4).

In some jurisdictions, there are also local laws that override Microsoft’s agreements and permit all copying for your personal, non-commercial use as long as you have legally obtained the original on a permanent basis—so if you purchased a second-hand laptop that came with a legal copy of Vista, you may copy its `.ttf` files to another GNU/Linux machine for your personal use. But the UK’s October 2014 “private copying exception” (a) didn’t apply to computer programs—TrueType hinting code might well count as a “program”—and (b) was quashed by a judicial review on 17<sup>th</sup> July 2015 (and the UK government said it was “not intending to take further action to reintroduce an exception”), so it seems if you are in the UK you must now rely only on the permissions Microsoft itself gave—which, if my interpretation above is correct, means you must ensure the content you display was originally created on a Windows system.

If you *do* determine it’s legal for you to use Microsoft YaHei in your particular circumstances, you can enable it for one non-root user of a modern GNU/Linux environment by adding the `.ttf` file to your `~/.fonts/TTF` directory (create it if it’s not there) and running `fc-cache -vf` (you can verify this worked by checking that `fc-list "Microsoft YaHei"` produces output).

It should then be available to Windows applications in WINE, although not all applications can be set to use it because WINE’s font-selection API doesn’t quite work like real Windows—a workaround is to edit `.wine/system.reg` and under `[Software\\Microsoft\\Windows NT\\CurrentVersion\\FontSubstitutes]` set `"MS Shell Dlg"="Microsoft YaHei"` then use “MS Shell Dlg” in the application (and if *that* doesn’t work, try adding a font like Droid Sans Fallback to the system and set `"Droid Sans Fallback"="Microsoft YaHei"` in `FontSubstitutes` so it can be selected that way).

If YaHei is the *only* Chinese font on the system (e.g. on a VM) then Web browsers like Firefox should select it by default, in which case you’d better check it’s legal and that all Chinese text you display was created on a Windows system. If other Chinese fonts are installed, and you are rendering a website with CSS code that does not call for Microsoft YaHei but you wish to use it (if you’ve determined it’s legal and the website was created on a Windows system), you could either edit the CSS (e.g. via Web Adjuster’s `--headAppend="<style> *:lang(cmn) { font-family: Microsoft Yahei !important } </style>" --js-upstream`), or else add an override in `~/.fonts.conf` but this is less reliable across rendering engines.

This is **not legal advice**—I’m a computer scientist, not a lawyer; take my observations at your own risk! But it does seem like a loophole to me.

Copyright and Trademarks:
All material © Silas S. Brown unless otherwise stated.
Android is a trademark of Google LLC.
CJK was a registered trademark of The Research Libraries Group, Inc. and subsequently OCLC, but I believe the trademark has expired.
Firefox is a registered trademark of The Mozilla Foundation.
Linux is the registered trademark of Linus Torvalds in the U.S. and other countries.
Microsoft is a registered trademark of Microsoft Corp.
SimSun is a trademark of Zhongyi Electronic Co., Beijing, which is licensed to Microsoft.
TeX is a trademark of the American Mathematical Society.
TrueType is a trademark of Apple Inc., registered in the United States and other countries.
Unicode is a registered trademark of Unicode, Inc. in the United States and other countries.
Windows is a registered trademark of Microsoft Corp.
Any other [trademarks](https://ssb22.user.srcf.net/trademarks.html) I mentioned without realising are trademarks of their respective holders.
