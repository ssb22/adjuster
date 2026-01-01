
from https://ssb22.user.srcf.net/adjuster/screenshot.html (also [mirrored on GitLab Pages](https://ssb22.gitlab.io/adjuster/screenshot.html) just in case)

# Screenshotting Chinese Web documents for WeChat

This page is **not legal advice**—be sure that you have permissions under copyright law to share a copy of the Web document, and that it is legal to read in the country where your reader is located.

Reasons for sharing a screenshot instead of a link:
1. Technical problems on the receiver’s side prevent proper display of the page;
2. The server is unreliable or rapidly changes;
3. The page itself is innocent but the recipient’s network infrastructure blocks the domain it’s on because of something *else* on that domain or by mistake.

Reasons *not* to use screenshots:
1. Poor accessibility: if the recipient needs to copy/paste the text into dictionaries or other learning tools, read it with a speech synthesizer or reflow it to a different width, then this may require OCR which is unreliable;
2. No interactivity: pages where the recipient must enter information or follow links won’t work as screenshots.

## Creating a narrow-column screenshot

WeChat is normally used on mobile phones with narrow displays. As of 2018, any image it receives is first shown as a preview (usually taken from the middle); when the user taps to view it full-screen, the image is sized to fill the *width* of the display, but in the *vertical* direction the user is allowed to scroll (starting at the top). This makes it ideal to send screenshots of fixed width but unbounded height (within the size limits mentioned below), and such “tall, narrow images of text” are already used by people forwarding “fun” things around WeChat.

My [Web Adjuster](../README.md) can be used with Headless Chrome (or Firefox or PhantomJS) to create an appropriate “narrow-column screenshot” by configuring with a `js_interpreter` setting (ideally `HeadlessChrome`, but if you can’t install that then you could try the older `PhantomJS`), and with `--js_size=400 --viewsource` and append `.screenshot` to the end of the URL you give it.

On GNU/Linux I also recommend creating a `~/.fonts.conf` or `~/.config/fontconfig/fonts.conf` file (depending on which one the system uses) to switch off anti-aliasing, as non-antialiased text is usually more readable and makes for better compression in PNG files. Here is a [non-antialiasing fonts.conf](https://ssb22.user.srcf.net/setup/fontsconf.txt?/.fonts.conf).

There is a [possible loophole in Microsoft’s YaHei font license](yahei.md) that *might* allow you to use that font if you want to make the Chinese text look a little nicer at small pixel sizes. Usual disclaimers apply—I am not a lawyer.

## Size limits

You must be aware of [WeChat’s image size limits](https://ssb22.user.srcf.net/s60/welimits.html)—basically the upper bound is 300 KiB, or 128K in certain (avoidable) circumstances.

You may also assemble up to 30 images into a WeChat “Note”, to be displayed as a continuous stack of images. These may display blurred until tapped unless you limit each one’s vertical dimension to about twice the horizontal (e.g. 400x800, giving you a total vertical capacity of 24,000 which is typically 3-4x what you’d get if doing the same thing in individual images if the page makes moderate use of graphics). The more you exceed this per-image vertical size, the more the WeChat app will blur the image before it’s tapped, even though the image’s physical display size remains in correct proportion.

If you wish to crop out an irrelevant section of the page—for example a box of links at the bottom, which won’t be usable on a screenshot—you can either write a site-specific rule for it in Web Adjuster, or else load the screenshot into The GIMP, select and cut unwanted *full-width* areas to transparent (making sure **not** to cut from the text or credits—don’t misrepresent or plagiarise!), export to PNG, and use a command like:

`python2 -c 'f="test.png"; from PIL import Image as I; i=I.open(f); b=i.tobytes(); c="".join(b[n:n+4] for n in xrange(0,len(b),4) if ord(b[n+3])); I.frombytes("RGBA", (i.width, len(c)/i.width/4), c) .save(f, optimize=True)'`

(command works only if you cut full-width areas).

If the page has many pictures but little text, consider using JPG instead. With ImageMagick, use:

`convert input.png -define jpeg:extent=300KiB output.jpg`

(this option was introduced in version 6.5.8-1 and uses ‘binary chop’ to find the most suitable JPEG quality setting within 8 tries; if you have a version between 6.9.1-0 and 6.9.2-4 you should also add `-quality 100` which is ignored by higher versions). If you are sequencing multiple images into a “Note”, you can choose between PNG and JPEG on an image-by-image basis.

Copyright and Trademarks:
All material © Silas S. Brown unless otherwise stated.
Firefox is a registered trademark of The Mozilla Foundation.
ImageMagick is a registered trademark of ImageMagick Studio LLC.
Linux is the registered trademark of Linus Torvalds in the U.S. and other countries.
Microsoft is a registered trademark of Microsoft Corp.
WeChat is a trademark of Tencent Holdings Limited.
Any other [trademarks](https://ssb22.user.srcf.net/trademarks.html) I mentioned without realising are trademarks of their respective holders.
