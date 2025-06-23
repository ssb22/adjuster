# adjuster

Web Adjuster + Annotator Generator + TermLayout from http://ssb22.user.srcf.net/adjuster/

(also mirrored at http://ssb22.gitlab.io/adjuster just in case, and available via `pip install adjuster` or `pip install annogen` or `pip install termlayout`, or `pipx run adjuster` or `pipx run annogen` or `pipx run termlayout`)

Web Adjuster
============

Web Adjuster is a Tornado-based, domain-rewriting proxy for applying custom processing to Web pages. It is particularly meant for users of smartphones etc as these might not support browser extensions. Web Adjuster can:

* Add a custom stylesheet to change size, layout and colours

* Add custom Javascript to all pages, allowing many desktop browser extensions to work as-is on a smartphone or tablet

* Run a custom program to change the markup, or to change or annotate text for language tools (see for example Annotator Generator)

* Render images for a language or text size not supported by the browser (this function requires the Python Imaging Library and suitable fonts)

* Down-sample MP3 audio to save bandwidth, and add plain text versions of PDF and EPUB files (helper programs are required for these functions)

* Remove problematic markup from pages, etc.

_Domain rewriting_ means you do not need to be able to change the device’s proxy settings—you simply go to a different address. However, _only the domain part is different_, so most in-site scripting should work as-is, without needing delicate alterations to its URI handling. For example, if you have a server called `adjuster.example.org` and you want to see `www.example.com`, simply go to `www.example.com.adjuster.example.org`. Your server ideally needs a wildcard domain, but you can manage without one in some cases, and Web Adjuster can also be a “real” HTTP proxy for local use on a desktop etc.

Because it is based on a single-threaded event-driven Tornado server, Web Adjuster can efficiently handle connections even on a low-power machine like the original Raspberry Pi. (Add-on programs run in other threads, but this is seldom a slow-down in practice.) Tornado also makes Web Adjuster easier to set up: it is a separate, self-contained server that doesn’t need to be worked into the configuration of another one—it can listen on an alternate port (and can be password protected)—but if you prefer you can configure it to share port 80 with another server.

Installation
------------

Make sure Tornado is on the system.  If you have root access to a GNU/Linux box, try `sudo apt-get install python-tornado` or `sudo pip install tornado` (on a Mac you might need sudo easy_install pip first).  If you don’t have root access, try `pip install tornado --user` and if all else fails then with Python 2.6 or 2.7 you can download the [old version 2.4.1](https://files.pythonhosted.org/packages/2b/29/c8590fd2072afd307412277a4505e282225425d89e556e2cc223eb2ecad7/tornado-2.4.1.tar.gz), unpack it and use its `tornado` subdirectory. On Windows, the easiest way is probably to install Cygwin, install its `python` package, and do something like `wget http://peak.telecommunity.com/dist/ez_setup.py && python ez_setup.py && easy_install pip && pip install tornado`

Then run adjuster.py with the appropriate options (see below), or use it in a WSGI application (see section at end).

Web Adjuster is free software licensed under the Apache License, Version 2.0 (this is also the license used by Tornado itself). If you use it in a good project, I’d appreciate hearing about it.

Annotator Generator
===================

Annotator Generator is an examples-driven generator of fast text annotators. “Annotate” in this context means to add pronunciation or other information to each word, and/or to split text into words in a language that does not use spaces.

* You supply a corpus of pre-annotated texts for Annotator Generator to work out the rules and exceptions

* Annotator Generator creates table-driven code in C, Java, Javascript, Dart or Python with 2 and 3 compatibility

* The resulting program should be able to annotate any text that contains words or phrases similar to those found in the examples

* It can output the annotations alone or it can combine them with the original text using HTML Ruby markup or simple braces

* If anything is unclear (didn’t happen in the examples, or there’s not enough context to figure out which example should be applied) then the program will leave it unannotated so you can pass it to a backup annotation program if you have one.

* If you have no backup annotator then try setting the `-y` option, which makes Annotator Generator try harder to find context-independent rules with context-dependent exceptions, so as to annotate as much text as possible.

* Generated annotators can act as filters for Web Adjuster; options are also provided for generating Android apps, browser extensions, and clipboard annotators for Windows and Windows Mobile, or you could format the annotations on a Unix terminal

Legal considerations
--------------------

Annotator code will contain individual words and some phrases from the original corpus (and these can be read even by people who do not have the unannotated version); with regards to copyright law, I expect the annotator code will count as an “index” to the collection, the copyright of which exists separately to that of the original collection, but laws do vary by country and I am not a solicitor so please act judiciously.

Legally obtaining that original annotated corpus is up to you. _If you are in the UK_ the government says non-commercial text mining is allowed (terms of use prohibiting non-commercial mining are unenforceable), provided you:

1. respect network stability (i.e. wait a long time between each download),

2. connect directly to the publisher (this law bypasses the publisher’s terms of use, not those of third-party search engines like Google),

3. use the result only for mining, not for republishing the original text (so you can’t publish your unprocessed crawl dumps either),

4. and still respect any prohibitions against sharing whatever mining tools you made for the site (as this law is only about text mining, not about the sharing of tools).

Laws outside the UK are different (and I’m not a lawyer) so check carefully. Gao et al 2020’s [paper on “The Pile”](https://arxiv.org/abs/2101.00027) claims published crawl dumps with limited processing *might* be permissible under American copyright law as transformative fair use, but I’m not sure how legally watertight their argument is: it might be safer to keep unlicensed parts of the corpus private and publish only the resulting index.

If the website’s terms don’t actually prohibit writing an unpublished scraper for non-commercial mining purposes, perhaps you won’t need a legal exception for the crawling part—but you should still respect their bandwidth and do it slowly, both for moral reasons (it’s the right thing to do) and pragmatic ones (you won’t want their sysadmins and service providers taking action against you).

Citation
--------

If you need to cite a peer-reviewed paper:

Silas S. Brown.  Web Annotation with Modified-Yarowsky and Other Algorithms.  Overload 112 (December 2012) pp.4-7.

TermLayout
==========

TermLayout is a text-mode HTML formatter for Unix terminals which supports:

* Ruby markup (multiple rt and rb elements are stacked)

* Tables (including nesting and alignment)

* Wide characters (uses locale settings from LC_CTYPE, LANG etc)

* Smaller terminal sizes. In some cases a table will still end up being wider than the terminal and not easily reﬂowable; if that happens then at least each cell should fit. But in many cases TermLayout can arrange for no horizontal scrolling to be necessary.

Unrecognised markup is left in the output for inspection.

TermLayout is _not_ a Web browser: it has no facilities for navigating links. It is meant only for formatting text on a terminal using HTML markup. I wrote it when I wanted to page through a document with Ruby markup in fbterm but couldn’t find a text-mode browser that would format this markup correctly.

If you are using TermLayout with an annotator generated by Annotator Generator, you might also be interested in `tmux-annotator.sh` which sets up tmux with a “hotkey” to annotate the current screen and display the result in TermLayout.

Options for Web Adjuster v3.244
============

General options
---------------

`--config` 
: Name of the configuration file to read, if any. The process's working directory will be set to that of the configuration file so that relative pathnames can be used inside it. Any option that would otherwise have to be set on the command line may be placed in this file as an option="value" or option='value' line (without any double-hyphen prefix). Multi-line values are possible if you quote them in """...""", and you can use standard \ escapes. You can also set config= in the configuration file itself to import another configuration file (for example if you have per-machine settings and global settings). If you want there to be a default configuration file without having to set it on the command line every time, an alternative option is to set the ADJUSTER_CFG environment variable.

`--version` 
: Just print program version and exit

Network listening and security settings
---------------------------------------

`--port`  (default 28080)
: The port to listen on. Setting this to 80 will make it the main Web server on the machine (which will likely require root access on Unix); setting it to 0 disables request-processing entirely (for if you want to use only the Dynamic DNS option); setting it to -1 selects a local port in the ephemeral port range, in which case address and port will be written in plain form to standard output if it's not a terminal and --background is set (see also --just-me).

`--publicPort`  (default 0)
: The port to advertise in URLs etc, if different from 'port' (the default of 0 means no difference). Used for example if a firewall prevents direct access to our port but a server like nginx is configured to forward incoming connections.

`--address` 
: The address to listen on. If unset, will listen on all IP addresses of the machine. You could for example set this to localhost if you want only connections from the local machine to be received, which might be useful in conjunction with --real_proxy.

`--password` 
: The password. If this is set, nobody can connect without specifying ?p= followed by this password. It will then be sent to them as a cookie so they don't have to enter it every time. Notes: (1) If wildcard_dns is False and you have multiple domains in host_suffix, then the password cookie will have to be set on a per-domain basis. (2) On a shared server you probably don't want to specify this on the command line where it can be seen by process-viewing tools; use a configuration file instead. (3) When not in HTML-only mode, browsers that send AJAX requests without cookies might have problems when password is set.

`--password-domain` 
: The domain entry in host_suffix to which the password applies. For use when wildcard_dns is False and you have several domains in host_suffix, and only one of them (perhaps the one with an empty default_site) is to be password-protected, with the others public. If this option is used then prominentNotice (if set) will not apply to the passworded domain. You may put the password on two or more domains by separating them with slash (/).

`--auth-error`  (default Authentication error)
: What to say when password protection is in use and a correct password has not been entered. HTML markup is allowed in this message. As a special case, if this begins with http:// or https:// then it is assumed to be the address of a Web site to which the browser should be redirected. If the markup begins with a * then this is removed and the page is returned with code 200 (OK) instead of 401 (authorisation required).

`--open-proxy`  (default False)
: Whether or not to allow running with no password. Off by default as a safeguard against accidentally starting an open proxy.

`--prohibit`  (default wiki.*action=edit)
: Comma-separated list of regular expressions specifying URLs that are not allowed to be fetched unless --real_proxy is in effect. Browsers requesting a URL that contains any of these will be redirected to the original site. Use for example if you want people to go direct when posting their own content to a particular site (this is of only limited use if your server also offers access to any other site on the Web, but it might be useful when that's not the case). Include ^https in the list to prevent Web Adjuster from fetching HTTPS pages for adjustment and return over normal HTTP. This access is enabled by default now that many sites use HTTPS for public pages that don't really need to be secure, just to get better placement on some search engines, but if sending confidential information to the site then beware you are trusting the Web Adjuster machine and your connection to it, plus its certificate verification might not be as thorough as your browser's.

`--prohibitUA`  (default TwitterBot)
: Comma-separated list of regular expressions which, if they occur in browser strings, result in the browser being redirected to the original site. Use for example if you want certain robots that ignore robots.txt to go direct.

`--real-proxy`  (default False)
: Whether or not to accept requests with original domains like a "real" HTTP proxy.  Warning: this bypasses the password and implies open_proxy.  Off by default.

`--via`  (default True)
: Whether or not to update the Via: and X-Forwarded-For: HTTP headers when forwarding requests

`--uavia`  (default True)
: Whether or not to add to the User-Agent HTTP header when forwarding requests, as a courtesy to site administrators who wonder what's happening in their logs (and don't log Via: etc)

`--robots`  (default False)
: Whether or not to pass on requests for /robots.txt.  If this is False then all robots will be asked not to crawl the site; if True then the original site's robots settings will be mirrored.  The default of False is recommended.

`--just-me`  (default False)
: Listen on localhost only, and check incoming connections with an ident server (which must be running on port 113) to ensure they are coming from the same user.  This is for experimental setups on shared Unix machines; might be useful in conjuction with --real_proxy.  If an ident server is not available, an attempt is made to authenticate connections via Linux netstat and /proc.

`--one-request-only`  (default False)
: Shut down after handling one request.  This is for use in inefficient CGI-like environments where you cannot leave a server running permanently, but still want to start one for something that's unsupported in WSGI mode (e.g. js_reproxy): run with --one_request_only and forward the request to its port.  You may also wish to set --seconds if using this.

`--seconds`  (default 0)
: The maximum number of seconds for which to run the server (0 for unlimited).  If a time limit is set, the server will shut itself down after the specified length of time.

`--stdio`  (default False)
: Forward standard input and output to our open port, in addition to being open to normal TCP connections.  This might be useful in conjuction with --one-request-only and --port=-1.

`--upstream-proxy` 
: address:port of a proxy to send our requests through. This can be used to adapt existing proxy-only mediators to domain rewriting, or for a caching proxy. Not used for ip_query_url options or fasterServer. If address is left blank (just :port) then localhost is assumed and https URLs will be rewritten into http with altered domains; you'll then need to set the upstream proxy to send its requests back through the adjuster (which will listen on localhost:port+1 for this purpose) to undo that rewrite. This can be used to make an existing HTTP-only proxy process HTTPS pages.

`--ip-messages` 
: Messages or blocks for specific IP address ranges (IPv4 only).  Format is ranges|message|ranges|message etc, where ranges are separated by commas; can be individual IPs, or ranges in either 'network/mask' or 'min-max' format; the first matching range-set is selected.  If a message starts with * then its ranges are blocked completely (rest of message, if any, is sent as the only reply to any request), otherwise message is shown on a 'click-through' page (requires Javascript and cookies).  If the message starts with a hyphen (-) then it is considered a minor edit of earlier messages and is not shown to people who selected `do not show again' even if they did this on a different version of the message.  Messages may include HTML.

DNS and website settings
------------------------

`--host-suffix`  (default is the machine's domain name)
: The last part of the domain name. For example, if the user wishes to change `www.example.com` and should do so by visiting `www.example.com.adjuster.example.org`, then host_suffix is adjuster.example.org. If you do not have a wildcard domain then you can still adjust one site by setting wildcard_dns to False, host_suffix to your non-wildcard domain, and default_site to the site you wish to adjust. If you have more than one non-wildcard domain, you can set wildcard_dns to False, host_suffix to all your domains separated by slash (/), and default_site to the sites these correspond to, again separated by slash (/); if two or more domains share the same default_site then the first is preferred in links and the others are assumed to be for backward compatibility. If wildcard_dns is False and default_site is empty (or if it's a /-separated list and one of its items is empty), then the corresponding host_suffix gives a URL box and sets its domain in a cookie (and adds a link at the bottom of pages to clear this and return to the URL box), but this should be done only as a last resort: you can browse only one domain at a time at that host_suffix, and unless you use HTML-only mode, most links and HTTP redirects to other domains will leave the adjuster (which can negatively affect sites that use auxiliary domains for scripts etc and check Referer, unless you ensure these auxiliary domains are listed elsewhere in default_site), and browsers that don't include cookies in their AJAX requests will have problems. Also, the sites you visit at that host_suffix might be able to see some of each other's cookies etc (leaking privacy) although the URL box page will try to clear site cookies.

`--default-site` 
: The site to fetch from if nothing is specified before host_suffix, e.g. example.org (add .0 at the end to specify an HTTPS connection, but see the 'prohibit' option). If default_site is omitted then the user is given a URL box when no site is specified; if it is 'error' then an error is shown in place of the URL box (the text of the error depends on the settings of wildcard_dns and real_proxy).

`--search-sites` 
: Comma-separated list of search sites to be made available when the URL box is displayed (if default_site is empty). Each item in the list should be a URL (which will be prepended to the search query), then a space, then a short description of the site. The first item on the list is used by default; the user can specify other items by making the first word of their query equal to the first word of the short description. Additionally, if some of the letters of that first word are in parentheses, the user may specify just those letters. So for example if you have an entry `http://search.example.com/?q=` (e)xample, and the user types 'example test' or 'e test', it will use `http://search.example.com/?q=test`

`--urlbox-extra-html` 
: Any extra HTML you want to place after the URL box (when shown), such as a paragraph explaining what your filters do etc.

`--urlboxPath`  (default /)
: The path of the URL box for use in links to it. This might be useful for wrapper configurations, but a URL box can be served from any path on the default domain. If however urlboxPath is set to something other than / then efforts are made to rewrite links to use it more often when in HTML-only mode with cookie domain, which might be useful for limited-server situations. You can force HTML-only mode to always be on by prefixing urlboxPath with *

`--wildcard-dns`  (default True)
: Set this to False if you do **not** have a wildcard domain and want to process only default_site. Setting this to False does not actually prevent other sites from being processed (for example, a user could override their local DNS resolver to make up for your lack of wildcard domain); if you want to really prevent other sites from being processed then you should get nginx or similar to block incoming requests for the wrong domain. Setting wildcard_dns to False does stop the automatic re-writing of links to sites other than default_site. Leave it set to True to have **all** sites' links rewritten on the assumption that you have a wildcard domain.

`--urlscheme`  (default http://)
: Default URL scheme to use when referring to our other subdomains.  Setting this to // or https:// means you will need a wildcard TLS certificate (or a multi-subdomain one with wildcard-limit set), but leaving it at http:// means you may have only an unencrypted connection to at least some of the adjuster session.

`--alt-dot` 
: String to place before host_suffix if the adjuster is run behind an SSL/TLS terminator that lacks certificates for subdomains beyond host_suffix but can still route such subdomains to the adjuster if separated by this string instead of a dot.  Beware this leads to an undesirable situation with subdomain-shared cookies: either they'll be set on only one domain instead of its subdomains (default), breaking some websites (and breaking the password option if you use it), or if you add a * before the value of alt-dot they can be sent not only to all adjusted domains but also to all other domains at the same level as the adjuster i.e. other users of the provider (use this only for temporary experimental accounts if you know what you're doing, and it won't work on modern browsers if the provider has listed their upper levels in Mozilla's top-level domains on which not even Javascript can set cookies).  If possible, it's better to avoid this option and instead use a load balancer providing a shorter host_suffix, although if that doesn't have a wildcard certificate you'll be on unencrypted HTTP, unless you can set a multi-subdomain certificate with wildcard-limit set.

`--wildcard-limit` 
: Comma separated list of domains to process via wildcard-dns, if not unlimited.  Use this if you have a wildcard DNS entry but not a wildcard TLS certificate, but your TLS certificate can cover specific subdomains of the form www-example-net-0.adjuster.example.org and you wish to adjust these domains (in this example wildcard-limit should include `www.example.net).`  Unlike slash-separated default-site, this allows cookie sharing between subdomains.  Any domains not listed will be sent out of the adjuster.

General adjustment options
--------------------------

`--default-cookies` 
: Semicolon-separated list of name=value cookies to send to all remote sites, for example to set preferences. Any cookies that the browser itself sends will take priority over cookies in this list. Note that these cookies are sent to **all** sites. You can set a cookie only on a specific browser by putting (browser-string) before the cookie name, e.g. (iPad)x=y will set x=y only if 'iPad' occurs in the browser string (to match more than one browser-string keyword, you have to specify the cookie multiple times).

`--headAppend` 
: Code to append to the HEAD section of every HTML document that has a BODY. Use for example to add your own stylesheet links and scripts. Not added to documents that lack a BODY such as framesets.

`--headAppendCSS` 
: URL of a stylesheet to add to the HEAD section of every HTML document that has a BODY.  This option automatically generates the LINK REL=... markup for it, and also tries to delete the string '!important' from other stylesheets, to emulate setting this stylesheet as a user CSS.  Additionally, it is not affected by --js-upstream as headAppend is.  You can also include one or more 'fields' in the URL, by marking them with %s and following the URL with options e.g. `http://example.org/style%s-%s.css;1,2,3;A,B` will allow combinations like style1-A.css or style3-B.css; in this case appropriate selectors are provided with the URL box (values may optionally be followed by = and a description), and any visitors who have not set their options will be redirected to the URL box to do so.

`--protectedCSS` 
: A regular expression matching URLs of stylesheets with are "protected" from having their '!important' strings deleted by headAppendCSS's logic. This can be used for example if you are adding scripts to allow the user to choose alternate CSS files in place of headAppendCSS, and you wish the alternate CSS files to have the same status as the one supplied in headAppendCSS.

`--cssName` 
: A name for the stylesheet specified in headAppendCSS, such as "High Contrast".  If cssName is set, then the headAppendCSS stylesheet will be marked as "alternate", with Javascript links at the bottom of the page for browsers that lack their own CSS switching options.  If cssName begins with a * then the stylesheet is switched on by default; if cssName begins with a # then the stylesheet is switched on by default only if the browser reports system dark mode; if cssName is not set then the stylesheet (if any) is always on.

`--cssNameReload`  (default IEMobile 6, IEMobile 7, IEMobile 8, Opera Mini, Opera Mobi, rekonq, MSIE 5, MSIE 6, MSIE 7, MSIE 9, MSIE 10)
: List of (old) browsers that require alternate code for the cssName option, which is slower as it involves reloading the page on CSS switches.  Use this if the CSS switcher provided by cssName does nothing on your browser.

`--cssHtmlAttrs` 
: Attributes to add to the BODY element of an HTML document when cssNameReload is in effect (or when it would be in effect if cssName were set). This is for old browsers that try to render the document first and apply CSS later. Example: 'text="yellow" bgcolor="black"' (not as flexible as CSS but can still make the rendering process less annoying). If headAppendCSS has "fields" then cssHtmlAttrs can list multiple sets of attributes separated by ; and each set corresponds with an option in the last field of headAppendCSS.

`--headAppendRuby`  (default False)
: Convenience option which adds CSS and Javascript code to the HTML body that tries to ensure simple RUBY markup displays legibly across all modern browsers; this might be useful if you used Annotator Generator to make the htmlFilter program. (The option is named 'head' because it used to add markup to the HEAD; this was moved to the BODY to work around browser bugs.)

`--highlighting` 
: Convenience option which adds CSS and Javascript code to add a text-highlighting option to some browsers. If set, this option should be set to a comma-separated list of available colours (please ensure there's at least one for each stylesheet colour scheme likely to be in use); won't work well with --render because images are not highlighted. Highlights are saved in the browser, but might load incorrectly if the page's text changes between sessions.

`--bodyAppend` 
: Code to append to the BODY section of every HTML document that has one. Use for example to add a script that needs to be run after the rest of the body has been read, or to add a footer explaining how the page has been modified. See also prominentNotice.

`--bodyAppendGoesAfter` 
: If this is set to a regular expression matching some text or HTML code that appears verbatim in the body section, the code in bodyAppend will be inserted after the last instance of this regular expression (case sensitive) instead of at the end of the body. Use for example if a site styles its pages such that the end of the body is not a legible place for a footer.

`--bodyPrepend` 
: Code to place at the start of the BODY section of every HTML document that has one.

`--prominentNotice` 
: Text to add as a prominent notice to processed sites (may include HTML). If the browser has sufficient Javascript support, this will float relative to the browser window and will contain an 'acknowledge' button to hide it (for the current site in the current browsing session). Use prominentNotice if you need to add important information about how the page has been modified. If you set prominentNotice to the special value "htmlFilter", then the output of the htmlFilter option (if any) will be placed as a prominent notice; this can be used if you want to provide extra information or links derived from the content of the page. Note: if you include Javascript document.write() code in prominentNotice, check that document.readyState is not 'complete' or you might find the document is erased on some website/browser combinations when a site script somehow causes your script to be re-run after the document stream is closed. In some rare cases you might also need to verify that document.cookie does not contain _WA_warnOK=1

`--staticDocs` 
: url#path of static documents to add to every website, e.g. /_myStatic/#/var/www (make sure the first part is something not likely to be used by the websites you visit). This can be used to supply extra Javascript (e.g. for bodyPrepend to load) if it needs to be served from the same domain. The password option does not apply to staticDocs.

`--delete` 
: Comma-separated list of regular expressions to delete from HTML documents. Can be used to delete selected items of Javascript and other code if it is causing trouble for your browser. Will also delete from the text of pages; use with caution.

`--delete-css` 
: Comma-separated list of regular expressions to delete from CSS documents (but not inline CSS in HTML); can be used to remove, for example, dimension limits that conflict with annotations you add, as an alternative to inserting CSS overrides.  In rare cases you might want to replace the deleted regexp with another, in which case you can use @@ to separate the two, and a second @@ can be used to specify a string in the CSS URL that must be present for the operation to take effect (this could be combined with a codeChanges to add query parameters to the URL if you want the change to occur only when the CSS is loaded from specific HTML pages).

`--delete-doctype`  (default False)
: Delete the DOCTYPE declarations from HTML pages. This option is needed to get some old Webkit browsers to apply multiple CSS files consistently.

`--deleteOmit`  (default iPhone, iPad, Android, Macintosh)
: A list of browsers that do not need the delete and delete-doctype options to be applied. If any of these strings occur in the user-agent then these options are disabled for that request, on the assumption that these browsers are capable enough to cope with the "problem" code. Any delete-css option is still applied however.

`--cacheOmit`  (default IEMobile)
: A list of browsers that cannot be trusted to provide correct Cache-Control headers. Use this if your browser fails to renew data when you press Reload.

`--zeroWidthDelete`  (default IEMobile, MSIE 6)
: A list of (old) browsers that cannot be relied on to process Unicode zero-width space (U+200b) correctly and need it removed from websites

`--codeChanges` 
: Several lines of text specifying changes that are to be made to all HTML and Javascript code files on certain sites; use as a last resort for fixing a site's scripts. This option is best set in the configuration file and surrounded by r"""...""". The first line is a URL prefix (just "http" matches all); append a # to match an exact URL instead of a prefix, and #+number (e.g. #1 or #2) to match an exact URL and perform the change only that number of times in the page.  The second line is a string of code to search for, and the third is a string to replace it with. Further groups of URL/search/replace lines may follow; blank lines and lines starting with # are ignored. If the 'URL prefix' starts with a * then it is instead a string to search for within the code of the document body; any documents containing this code will match; thus it's possible to write rules of the form 'if the code contains A, then replace B with C'. This processing takes place before any 'delete' option takes effect so it's possible to pick up on things that will be deleted, and it occurs after the domain rewriting so it's possible to change rewritten domains in the search/replace strings (but the URL prefix above should use the non-adjusted version).

`--boxPrompt`  (default Website to adjust)
: What to say before the URL box (when shown); may include HTML; for example if you've configured Web Adjuster to perform a single specialist change that can be described more precisely with some word other than 'adjust', you might want to set this.

`--viewsource`  (default False)
: Provide a "view source" option. If set, you can see a page's pre-adjustment source code, plus client and server headers, by adding ".viewsource" to the end of a URL (after any query parameters etc)

`--htmlonly-mode`  (default True)
: Provide a checkbox allowing the user to see pages in "HTML-only mode", stripping out images, scripts and CSS; this might be a useful fallback for very slow connections if a site's pages bring in many external files and the browser cannot pipeline its requests. The checkbox is displayed by the URL box, not at the bottom of every page.

`--htmlonly-css`  (default False)
: Leave images and CSS in the page when in "HTML-only mode", removing only scripts

`--mailtoPath`  (default /@mail@to@__)
: A location on every adjusted website to put a special redirection page to handle mailto: links, showing the user the contents of the link first (in case a mail client is not set up). This must be made up of URL-safe characters starting with a / and should be a path that is unlikely to occur on normal websites and that does not conflict with renderPath. If this option is empty, mailto: links are not changed. (Currently, only plain HTML mailto: links are changed by this function; Javascript-computed ones are not.)

`--mailtoSMS`  (default Opera Mini, Opera Mobi, Android, Phone, Mobile)
: When using mailtoPath, you can set a comma-separated list of platforms that understand sms: links. If any of these strings occur in the user-agent then an SMS link will be provided on the mailto redirection page, to place the suggested subject and/or body into a draft SMS message instead of an email.

External processing options
---------------------------

`--htmlFilter` 
: External program(s) to run to filter every HTML document. If more than one program is specified separated by # then the user will be given a choice (see htmlFilterName option). Any shell command can be used; its standard input will get the HTML (or the plain text if htmlText is set), and it should send the new version to standard output. Multiple copies of each program might be run at the same time to serve concurrent requests. UTF-8 character encoding is used. If you are not able to run external programs then you could use a back-end server (specify an http:// or https:// URL and input is POSTed in the request body; if this back-end server is another Web Adjuster with submitPath and submitBookmarklet set then give its submitPath plus uA for its 1st filter, uB for its 2nd, etc), or use a Python function: specify * followed by the function name, and inject the function into the adjuster module from a wrapper script (which imports adjuster, sets adjuster.options.htmlFilter etc, injects the function and calls adjuster.main). The function should take a byte-string and return its modified version, and is run in the serving thread. See also htmlUrl and htmlonly_tell_filter options.

`--htmlFilterName` 
: A name for the task performed by htmlFilter. If this is set, the user will be able to switch it on and off from the browser via a cookie and some Javascript links at the bottom of HTML pages. If htmlFilter lists two or more options, htmlFilterName should list the same number plus one (again separated by #); the first is the name of the entire category (for example "filters"), and the user can choose between any one of them or none at all, hence the number of options is one more than the number of filters

`--htmlFilterCollapse`  (default 3)
: The maximum number of htmlFilterName options beyond which all but the first N-1 are hidden behind a "More" option on some browsers.

`--htmlJson`  (default False)
: Try to detect HTML strings in JSON responses and feed them to htmlFilter. This can help when using htmlFilter with some AJAX-driven sites. **Important**: Unless you also set the 'separator' option, the external program must preserve all newline characters, because multiple HTML strings in the same JSON response will be given to it separated by newlines, and the newlines of the output determine which fragment to put back where. (If you combine htmlJson with htmlText, the external program will see text in HTML in JSON as well as text in HTML, but it won't see text in HTML in JSON in HTML.)

`--htmlText`  (default False)
: Causes the HTML to be parsed, and only the text parts (not the markup) will be sent to htmlFilter. Useful to save doing HTML parsing in the external program. The external program is still allowed to include HTML markup in its output. **Important**: Unless you also set the 'separator' option, the external program must preserve all newline characters, because multiple text strings will be given to it separated by newlines, and the newlines of the output determine which modified string to put back where.

`--separator` 
: If you are using htmlFilter with htmlJson and/or htmlText, you can set separator to any text string to be used as a separator between multiple items of data when passing them to the external program. By default, newlines are used for this, but you can set it to any other character or sequence of characters that cannot be added or removed by the program. (It does not matter if a website's text happens to use the separator characters.) If separator is set, not only will it be used as a separator **between** items of data but also it will be added before the first and after the last item, thus allowing you to use an external program that outputs extra text before the first and after the last item. The extra text will be discarded. If however you do not set separator then the external program should not add anything extra before/after the document.

`--leaveTags`  (default script, style, title, textarea, option)
: When using htmlFilter with htmlText, you can set a comma-separated list of HTML tag names whose enclosed text should **not** be sent to the external program for modification. For this to work, the website must properly close these tags and must not nest them. (This list is also used for character-set rendering.)

`--stripTags`  (default wbr)
: When using htmlFilter with htmlText, you can set a comma-separated list of HTML tag names which should be deleted if they occur in any section of running text. For example, "wbr" (word-break opportunity) tags (listed by default) might cause problems with phrase-based annotators.

`--htmlUrl`  (default False)
: Add a line containing the document's URL to the start of what gets sent to htmlFilter (useful for writing filters that behave differently for some sites; not yet implemented for submitBookmarklet, which will show a generic URL). The URL line must not be included in the filter's response.

`--htmlonly-tell-filter`  (default False)
: Add a line showing the current status of "HTML-only mode" (see htmlonly_mode option) to the start of what gets sent to htmlFilter (before any htmlUrl if present), as "True" or "False" (must not be included in the filter's response).  This may be useful for filters that need to do extra processing if client-side scripts are removed.

`--submitPath` 
: If set, accessing this path (on any domain) will give a form allowing the user to enter their own text for processing with htmlFilter. The path should be one that websites are not likely to use (even as a prefix), and must begin with a slash (/). If you prefix this with a * then the * is removed and any password set in the 'password' option does not apply to submitPath. Details of the text entered on this form is not logged by Web Adjuster, but short texts are converted to compressed GET requests which might be logged by proxies etc.

`--submitPrompt`  (default Type or paste in some text to adjust)
: What to say before the form allowing users to enter their own text when submitPath is set (compare boxPrompt)

`--submitPromptTitle`  (default Upload Text)
: The title of the form allowing users to enter their own text when submitPath is set

`--submitPromptAction`  (default Upload)
: The button label for the form allowing users to enter their own text when submitPath is set

`--identifyAdjusterOnUploadedText`  (default True)
: Identify the Web Adjuster version at the bottom of the Uploaded Text result (you might want to set this to False if you're publicly running only a submitPath)

`--submitBookmarklet`  (default True)
: If submitPath and htmlFilter is set, and if browser Javascript support seems sufficient, then add one or more 'bookmarklets' to the submitPath page (named after htmlFilterName if provided), allowing the user to quickly upload text from other sites. This might be useful if for some reason those sites cannot be made to go through Web Adjuster directly. The bookmarklets should work on modern desktop browsers and on iOS and Android; they should cope with frames and with Javascript-driven changes to a page, and on some browsers an option is provided to additionally place the page into a frameset so that links to other pages on the same site can be followed without explicitly reactivating the bookmarklet (but this does have disadvantages—page must be reloaded + URL display gets 'stuck'—so it's left to the user to choose).

`--submitBookmarkletFilterJS`  (default !c.nodeValue.match(/^[ -~\s]*$/))
: A Javascript expression that evaluates true if a DOM text node 'c' should be processed by the 'bookmarklet' Javascript when submitPath and submitBookmarklet are set. To process **all** text, set this option to c.nodeValue.length, but if your htmlFilter will not change certain kinds of text then you can make the Javascript run more efficiently by not processing these (quote the expression carefully). The default setting will not process text that is all ASCII.

`--submitBookmarkletChunkSize`  (default 1024)
: Specifies the approximate number of characters at a time that the 'bookmarklet' Javascript will send to the server if submitPath and submitBookmarklet are set. Setting this too high could impair browser responsiveness, but too low will be inefficient with bandwidth and pages will take longer to finish.

`--submitBookmarkletDomain` 
: If set, specifies a domain to which the 'bookmarklet' Javascript should send its XMLHttpRequests, and ensures that they are sent over HTTPS if the 'bookmarklet' is activated from an HTTPS page (this is needed by some browsers to prevent blocking the XMLHttpRequest).  submitBookmarkletDomain should be a domain for which the adjuster (or an identically-configured copy) can receive requests on both HTTP and HTTPS, and which has a correctly-configured HTTPS front-end with valid certificate.

`--letsEncryptWarning`  (default False)
: Indicates that submitBookmarkletDomain (if set) has an HTTPS server that uses a certificate from LetsEncrypt, and we should warn users of certain old browsers that they won't accept it by default now LetsEncrypt's X3 expired at the end of September 2021

`--submitBookmarkletRemoveExistingRuby`  (default True)
: Specifies that 'bookmarklets' added to the submitPath page should remove all existing ruby on a page before running.  Use this for example if you expect to replace the text with ruby of a different kind of annotation.

Javascript execution options
----------------------------

`--js-interpreter` 
: Execute Javascript on the server for users who choose "HTML-only mode". You can set js_interpreter to PhantomJS, HeadlessChrome, HeadlessFirefox, Chrome, Firefox, or edbrowse (experimental), and must have the appropriate one installed, along with an appropriate version of Selenium (and ChromeDriver or GeckoDriver if appropriate) if not using edbrowse.  Non-headless Chrome or Firefox requires a display (and might not respond to manual window close) but may help work around bugs in some headless versions.  If you have multiple users, beware logins etc may be shared!  If a URL box cannot be displayed (no wildcard_dns and default_site is full, or processing a "real" proxy request) then htmlonly_mode auto-activates when js_interpreter is set, thus providing a way to partially Javascript-enable browsers like Lynx.  If --viewsource is enabled then js_interpreter URLs may also be followed by .screenshot

`--js-upstream`  (default False)
: Handle --headAppend, --bodyPrepend, --bodyAppend and --codeChanges upstream of our Javascript interpreter instead of making these changes as code is sent to the client, and make --staticDocs available to our interpreter as well as to the client.  This is for running experimental 'bookmarklets' etc with browsers like Lynx.

`--js-frames`  (default False)
: When using js_interpreter, append the content of all frames and iframes to the main document. This might help with bandwidth reduction and with sites that have complex cross-frame dependencies that can be broken by sending separate requests through the adjuster.

`--js-instances`  (default 1)
: The number of virtual browsers to load when js_interpreter is in use. Increasing it will take more RAM but may aid responsiveness if you're loading multiple sites at once.

`--js-429`  (default True)
: Return HTTP error 429 (too many requests) if js_interpreter queue is too long at page-prefetch time. When used with --multicore, additionally close to new requests any core that's currently processing its full share of js_instances.

`--js-restartAfter`  (default 10)
: When js_interpreter is in use, restart each virtual browser after it has been used this many times (0=unlimited); might help work around excessive RAM usage in PhantomJS v2.1.1. If you have many --js-instances (and hardware to match) you could also try --js-restartAfter=1 (restart after every request) to work around runaway or unresponsive PhantomJS processes.

`--js-restartMins`  (default 10)
: Restart an idle js_interpreter instance after about this number of minutes (0=unlimited); use this to stop the last-loaded page from consuming CPU etc indefinitely if no more requests arrive at that instance.  Not applicable when --js-restartAfter=1.

`--js-timeout1`  (default 30)
: When js_interpreter is in use, tell it to allow this number of seconds for initial page load. More time is allowed for XMLHttpRequest etc to finish (unless our client cuts the connection in the meantime).

`--js-timeout2`  (default 100)
: When js_interpreter is in use, this value in seconds is treated as a 'hard timeout': if a webdriver process does not respond at all within this time, it is assumed hung and emergency restarted.

`--js-retry`  (default True)
: If a js_interpreter fails, restart it and try the same fetch again while the remote client is still waiting

`--js-fallback`  (default X-Js-Fallback)
: If this is set to a non-empty string and a js_interpreter fails (even after js_retry if set), serve the page without Javascript processing instead of serving an error. The HTTP header specified by this option can tell the client whether or not Javascript was processed when a page is served.

`--js-reproxy`  (default True)
: When js_interpreter is in use, have it send its upstream requests back through the adjuster on a different port. This allows js_interpreter to be used for POST forms, fixes its Referer headers when not using real_proxy, monitors AJAX for early completion, prevents problems with file downloads, and enables the js_prefetch option.

`--js-prefetch`  (default True)
: When running with js_reproxy, prefetch main pages to avoid holding up a js_interpreter instance if the remote server is down.  Turn this off if you expect most remote servers to be up and you want to detect js_429 issues earlier.

`--js-UA` 
: Custom user-agent string for js_interpreter requests, if for some reason you don't want to use the JS browser's default (or the client's if js_reproxy is on and js_prefetch off). If you prefix js_UA with a * then the * is removed and the user-agent string is set by the upstream proxy (--js_reproxy) so scripts running in the JS browser itself will see its original user-agent.

`--js-images`  (default True)
: When js_interpreter is in use, instruct it to fetch images just for the benefit of Javascript execution. Setting this to False saves bandwidth but misses out image onload events.

`--js-size`  (default 1024x768)
: The virtual screen dimensions of the browser when js_interpreter is in use (changing it might be useful for screenshots)

`--js-links`  (default True)
: When js_interpreter is in use, handle some Javascript links via special suffixes on href URLs. Turn this off if you don't mind such links not working and you want to ensure URLs are unchanged modulo domain-rewriting.

`--js-multiprocess`  (default True)
: When js_interpreter is in use, handle the webdriver instances in completely separate processes (not just separate threads) when the multiprocessing module is available and working. Recommended: if a webdriver instance gets 'stuck' in a way that somehow hangs its controlling process, we can detect and restart it.

`--ssl-fork`  (default False)
: (Unix only) Run SSL-helper proxies as separate processes to stop the main event loop from being stalled by buggy SSL/TLS libraries. This costs RAM, but adding --multicore too will limit the number of helpers to one per core instead of one per port, so --ssl-fork --multicore is recommended if you want more js_interpreter instances than cores.

Server control options
----------------------

`--background`  (default False)
: (Unix only) Fork to the background as soon as the server has started. You might want to enable this if you will be running it from crontab, to avoid long-running cron processes.

`--restart`  (default False)
: (Unix only) Try to terminate any other process listening on our port number before we start. Useful if Web Adjuster is running in the background and you want to quickly restart it with new options. Note that no check is made to make sure the other process is a copy of Web Adjuster; whatever it is, if it has our port open, it is asked to stop.

`--stop`  (default False)
: (Unix only) Like 'restart', but don't replace the other process after stopping it. This option can be used to stop a background server (if it's configured with the same port number) without starting a new one.

`--install`  (default False)
: Try to install the program in the current user's Unix crontab as an @reboot entry, unless it's already there.  The arguments of the cron entry will be the same as the command line, with no directory changes, so make sure you are in the home directory before doing this.  The program will continue to run normally after the installation attempt.  (If you are on Cygwin then you might need to run cron-config also.)

`--pidfile` 
: Write our process ID to this file when running in the background, so you can set up a systemd service with Type=forking and PIDFile=this instead of using crontab. (Alternatively use 'pip install sdnotify' and run in the foreground with Type=notify.)

`--browser` 
: The Web browser command to run. If this is set, Web Adjuster will run the specified command (which is assumed to be a web browser), and will exit when this browser exits. This is useful in conjunction with --real_proxy to have a personal proxy run with the browser. You still need to set the browser to use the proxy; this can sometimes be done via browser command line or environment variables.

`--run` 
: A command to run that is not a browser. If set, Web Adjuster will run the specified command and will restart it if it stops. The command will be stopped when Web Adjuster is shut down. This could be useful, for example, to run an upstream proxy.

`--runWait`  (default 1)
: The number of seconds to wait before restarting the 'run' command if it fails

Media conversion options
------------------------

`--bitrate`  (default 0)
: Audio bitrate for MP3 files, or 0 to leave them unchanged. If this is set to anything other than 0 then the 'lame' program must be present. Bitrate is normally a multiple of 8. If your mobile device has a slow link, try 16 for speech.

`--askBitrate`  (default False)
: If True, instead of recoding MP3 files unconditionally, try to add links to "lo-fi" versions immediately after each original link so you have a choice.

`--pdftotext`  (default False)
: If True, add links to run PDF files through the 'pdftotext' program (which must be present if this is set). A text link will be added just after any PDF link that is found, so that you have a choice of downloading PDF or text; note that pdftotext does not always manage to extract all text (you can use --pdfomit to specify URL patterns that should not get text links). The htmlJson setting will also be applied to the PDF link finder, and see also the guessCMS option.

`--pdfomit` 
: A comma-separated list of regular expressions which, if any are found in a PDF link's URL, will result in a text link not being generated for that PDF link (although a conversion can still be attempted if a user manually enters the modified URL).  Use this to avoid confusion for PDF files you know cannot be converted.

`--epubtotext`  (default False)
: If True, add links to run EPUB files through Calibre's 'ebook-convert' program (which must be present), to produce a text-only option (or a MOBI option if a Kindle is in use). A text link will be added just after any EPUB link that is found, so that you have a choice of downloading EPUB or text. The htmlJson setting will also be applied to the EPUB link finder, and see also the guessCMS option.

`--epubtozip`  (default False)
: If True, add links to download EPUB files renamed to ZIP, as a convenience for platforms that don't have EPUB readers but can open them as ZIP archives and display the XHTML files they contain. The htmlJson setting will also be applied to the EPUB link finder, and see also the guessCMS option.

`--guessCMS`  (default False)
: If True, then the pdftotext, epubtotext and epubtozip options attempt to guess if a link is pointing to a PDF or EPUB file via a Content Management System (i.e. the URL does not end in .pdf or .epub, but contains something like ?format=PDF)

`--pdfepubkeep`  (default 200)
: Number of seconds to keep any generated text files from PDF and EPUB.  If this is 0, the files will be deleted immediately, but that might be undesirable: if a mobile phone browser has a timeout that takes effect before ebook-convert has finished (this can sometimes be the case with Opera Mini for example), it might be best to allow the user to wait a short time and re-submit the request, this time getting a cached response.

`--waitpage`  (default True)
: If the browser seems to be an interactive one, generate a 'please wait' page while converting PDF or EPUB files to text. Not effective if pdfepubkeep is set too low.

Character rendering options
---------------------------

`--render`  (default False)
: Whether to enable the character-set renderer. This functionality requires the Python Imaging Library and suitable fonts. The settings of htmlJson and leaveTags will also be applied to the renderer. Text from computed Javascript writes might not be rendered as images.

`--renderFont` 
: The font file to use for the character-set renderer (if enabled). This should be a font containing all the characters you want to render, and it should be in .TTF, .OTF or other Freetype-supported format (.PCF is sometimes possible if renderSize is set correctly, e.g. 16 for wenquanyi_12pt.pcf)

`--renderInvert`  (default False)
: If True, the character-set renderer (if enabled) will use a black background. Useful when you are also adding a stylesheet with a dark background.

`--renderSize`  (default 20)
: The height (in pixels) to use for the character-set renderer if it is enabled.

`--renderPath`  (default /@_)
: The location on every adjusted website to put the character-set renderer's images, if enabled. This must be made up of URL-safe characters starting with a / and should be a short path that is unlikely to occur on normal websites.

`--renderFormat`  (default png)
: The file format of the images to be created by the character-set renderer if it is enabled, for example 'png' or 'jpeg'.

`--renderRange` 
: The lowest and highest Unicode values to be given to the character-set renderer if it is enabled. For example 3000:A6FF for most Chinese characters. Multiple ranges are allowed. Any characters **not** in one of the ranges will be passed to the browser to render. If the character-set renderer is enabled without renderRange being set, then **all** text will be rendered to images.

`--renderOmit`  (default iPhone, iPad, Android, CrOS, Macintosh, Windows NT 6, Windows NT 10, Windows Phone OS, Lynx/2)
: A list of platforms that do not need the character-set renderer. If any of these strings occur in the user-agent then the character set renderer is turned off even if it is otherwise enabled, on the assumption that these platforms either have enough fonts already, or wouldn't show the rendered images anyway.

`--renderOmitGoAway`  (default False)
: If set, any browsers that match renderOmit will not be allowed to use the adjuster. This is for servers that are set to do character rendering only and do not have enough bandwidth for people who don't need this function and just want a proxy.

`--renderCheck` 
: If renderOmit does not apply to the browser, it might still be possible to check for native character-set support via Javascript. renderCheck can be set to the Unicode value of a character to be checked (try 802F for complete Chinese support); if the browser reports its width differently from known unprintable characters, we assume it won't need our renderer.

`--renderNChar`  (default 1)
: The maximum number of characters per image to be given to the character-set renderer if it is enabled. Keeping this low means the browser cache is more likely to be able to re-use images, but some browsers might struggle if there are too many separate images. Don't worry about Unicode "combining diacritic" codes: any found after a character that is to be rendered will be included with it without counting toward the renderNChar limit and without needing to be in renderRange.

`--renderWidth`  (default 0)
: The maximum pixel width of a 'word' when using the character-set renderer. If you are rendering a language that uses space to separate words, but are using only one or two characters per image, then the browser might split some words in the middle. Setting renderWidth to some value other than 0 can help to prevent this: any word narrower than renderWidth will be enclosed in a <nobr> element. (This will however be ineffective if your stylesheet overrides the behaviour of <nobr>.) You should probably not set renderWidth if you intend to render languages that do not separate words with spaces.

`--renderDebug`  (default False)
: If the character-set renderer is having problems, try to insert comments in the HTML source to indicate why.  The resulting HTML is not guaranteed to be well-formed, but it might help you debug a misbehaving htmlFilter.  This option may also insert comments in bad HTML before the htmlFilter stage even when the renderer is turned off.

`--renderName`  (default Fonts)
: A name for a switch that allows the user to toggle character set rendering on and off from the browser (via a cookie and Javascript links at the bottom of HTML pages); if set to the empty string then no switch is displayed. At any rate none is displayed when renderOmit applies.

Dynamic DNS options
-------------------

`--ip-change-command` 
: An optional script or other shell command to launch whenever the public IP address changes. The new IP address will be added as a parameter; ip_query_url must be set to make this work. The script can for example update any Dynamic DNS services that point to the server.

`--ip-change-tries`  (default 1)
: Number of times to run ip_change_command if it returns failure (0 means unlimited, which is not recommended).  For example, you can have the script return failure if it doesn't get either an "Updated" or an expected "not changed" response from a Dynamic DNS service (but it is not advisable to expect a host lookup to reflect the change immediately)

`--ip-change-delay`  (default 5)
: Number of seconds to delay between tries of ip_change_command if it fails

`--ip-query-url` 
: URL that will return your current public IP address, as a line of text with no markup added. Used for the ip_change_command option. You can set up a URL by placing a CGI script on a server outside your network and having it do: echo Content-type: text/plain ; echo ; echo $REMOTE_ADDR (but if you want your IPv4 address, ensure the adjuster machine and the outside server are not both configured for IPv6). If you have a known static IP address but still want to run an ip_change_command for it, you can set ip_query_url to the static IP address instead of a URL.

`--ip-query-url2` 
: Optional additional URL that might sometimes return your public IP address along with other information. This can for example be a status page served by a local router (`http://user:password@192.168...` is accepted, and if the password is the name of an existing file then its contents are read instead). If set, the following behaviour occurs: Once ip_check_interval has passed since the last ip_query_url check, ip_query_url2 will be queried at an interval of ip_check_interval2 (which can be short), to check that the known IP is still present in its response. Once the known IP is no longer present, ip_query_url will be queried again. This arrangement can reduce the load on ip_query_url while allowing a reduced ip_check_interval for faster response to IP changes, while not completely trusting the local router to report the correct IP at all times. (If it's notoriously unleriable then it might be best **not** to reduce ip_check_interval, in which case at least you'll get a faster response once the initial ip_check_interval wait has passed after the previous IP change; this however might not be suitable if you're behind a router that is frequently rebooting.) See also ip_query_aggressive if the router might report an IP change before connectivity is restored. You may also set ip_query_url2 to the special value 'upnp' if you want it to query a router via UPnP (miniupnpc package required).

`--ip-check-interval`  (default 8000)
: Number of seconds between checks of ip_query_url for the ip_change_command option

`--ip-check-interval2`  (default 60)
: Number of seconds between checks of ip_query_url2 (if set), for the ip_change_command option

`--ip-query-aggressive`  (default False)
: If a query to ip_query_url fails with a connection error or similar, keep trying again until we get a response. This is useful if the most likely reason for the error is that our ISP is down: we want to get the new IP just as soon as we're back online. However, if the error is caused by a problem with ip_query_url itself then this option can lead to excessive traffic, so use with caution. (Log entries are written when this option takes effect, and checking the logs is advisable.)

`--ip-force-interval`  (default 604800)
: Number of seconds before ip_change_command (if set) is run even if there was no IP change.  This is to let Dynamic DNS services know that we are still around.  Set to 0 to disable forced updates (a forced update will occur on server startup anyway), otherwise an update will occur on the next IP check after ip_force_interval has elapsed.

`--pimote` 
: Use an Energenie Pi-mote home control system to power-cycle the router when its Internet connection appears to be stuck in a bad state.  This option works only if Web Adjuster is running on the Raspberry Pi and as a user in the "gpio" group.  It must be set to R,S,I,D where R is the internal IP address of your router, S is the domain of your Internet service provider (assumed to be quick to look up), I is the IP provided by your router's built-in DNS when it's having trouble (e.g. Post Office Broadband's AMG1302-derived router responds with 219.87.158.116 which is presumably Zyxel's office in Taiwan), and D is the Pi-mote device ID (1 to 4 or all) used to switch it off and on again.  Power-cycling will be initiated if two queries to the router's DNS for its ISP domain either fail or return internalResponse, and it's assumed router caching will let us check status frequently without causing traffic.

Speedup options
---------------

`--useLXML`  (default False)
: Use the LXML library for parsing HTML documents. This is usually faster, but it can fail if your system does not have a good installation of LXML and its dependencies. Use of LXML libraries may also result in more changes to all HTML markup: this should be harmless for browsers, but beware when using options like bodyAppendGoesAfter then you might or might not be dealing with the original HTML depending on which filters are switched on.

`--usepycurl`  (default True)
: Use the pycurl library if a suitable version is available (setting this to False might save a little RAM at the expense of remote-server tolerance)

`--renderBlocks`  (default False)
: Treat all characters rendered by the character-set renderer as "blocks" that are guaranteed to have the same dimensions (true for example if you are using the renderer for Chinese characters only). This is faster than checking words individually, but it may produce misprints if given a range of characters whose dimensions do differ.

`--fasterServer` 
: Address:port of another instance of Web Adjuster to which we forward all traffic whenever it is available. When the other instance is not available, traffic will be handled by this one. Use for example if you have a slower always-on machine and a faster not-always-on machine and you want the slower machine to delegate to the faster machine when available. See also ipTrustReal.

`--ipTrustReal` 
: IP address of a machine that we trust, for example a machine that is using us as fasterServer. Any traffic coming from this machine with an X-Real-Ip header will be logged as though it originated at the value of its X-Real-Ip header. Setting this to * will cause X-Real-Ip to be trusted from **any** connection.

`--trust-XForwardedFor`  (default False)
: Like ipTrustReal but trusts X-Forwarded-For header from any IP if set to True (use this in an environment where the adjuster can be reached only via a load balancer etc)

`--fasterServerNew`  (default True)
: If fasterServer is set, assume it is running Web Adjuster v0.17 or later and use a more lightweight method of checking its availability. You might need to set this to False if for some reason you can't upgrade the fasterServer first.

`--machineName` 
: A name for the current machine to insert into the "Server" HTTP header for adjusted requests, for example to let users know if it's your faster or your slower machine that's currently serving them (although they'd need to inspect the headers to find out)

`--redirectFiles`  (default False)
: If, when not functioning as a "real" HTTP proxy, a URL is received that looks like it requires no processing on our part (e.g. an image or downloadable file that the user does not want converted), and if this is confirmed via a HEAD request to the remote server, then redirect the browser to fetch it directly and not via Web Adjuster. This takes bandwidth off the adjuster server, and should mean faster downloads, especially from sites that are better connected than the adjuster machine. However it might not work with sites that restrict "deep linking". (As a precaution, the confirmatory HEAD request is sent with a non-adjusted Referer header to simulate what the browser would send if fetching directly. If this results in an HTML "Referer denied" message then Web Adjuster will proxy the request in the normal way. This precaution might not detect **all** means of deep-linking denial though.)

`--upstream-guard`  (default True)
: Modify scripts and cookies sent by upstream sites so they do not refer to the cookie names that our own scripts use. This is useful if you chain together multiple instances of Web Adjuster, such as for testing another installation without coming out of your usual proxy. If however you know that this instance will not be pointed to another, you can set upstream_guard to False to save some processing.

`--skipLinkCheck` 
: Comma-separated list of regular expressions specifying URLs to which we won't try to add or modify links for the pdftotext, epubtotext, epubtozip, askBitrate or mailtoPath options.  This processing can take some time on large index pages with thousands of links; if you know that none of them are PDF, EPUB, MP3 or email links, or if you don't mind not processing any that are, then it saves time to skip this step for those pages.

`--extensions` 
: Name of a custom Python module to load to handle certain requests; this might be more efficient than setting up a separate Tornado-based server. The module's handle() function will be called with the URL and RequestHandler instance as arguments, and should return True if it processed the request, but anyway it should return as fast as possible. This module does **not** take priority over forwarding the request to fasterServer.

`--loadBalancer`  (default False)
: Set this to True if you have a default_site set and you are behind any kind of "load balancer" that works by issuing a GET / with no browser string. This option will detect such requests and avoid passing them to the remote site.

`--multicore`  (default False)
: (Linux and BSD) On multi-core CPUs, fork enough processes for all cores to participate in handling incoming requests. This increases RAM usage, but can help with high-load situations. Disabled on Mac due to unreliability (other cores can still be used for htmlFilter etc)

`--num-cores`  (default 0)
: Set the number of CPU cores for the multicore option (0 for auto-detect)

`--internalPort`  (default 0)
: The first port number to use for internal purposes when ssl_fork is in effect.  Internal ports needed by real_proxy (for SSL/TLS) and js_reproxy are normally allocated from the ephemeral port range, but if ssl_fork delegates to independent processes then some of them need to be at known numbers. The default of 0 means one higher than 'port'; several unused ports may be needed starting at this number. If your Tornado is modern enough to support reuse_port then you can have multiple Adjuster instances listening on the same port (e.g. for one_request_only) provided they have different internalPort settings when run with ssl_fork.  Note however that the --stop and --restart options will **not** distinguish between different internalPort settings, only 'port'.

`--fixed-ports`  (default False)
: Do not allocate ports (even internal ports) from the ephemeral port range even when this is otherwise possible. This option might help if you are firewalling your loopback interface and want to write specific exceptions (although that still won't work if you're using js_interpreter=HeadlessChrome or similar which opens its own ephemeral ports as well: use containers if you're concerned). Fixed ports may result in failures if internal ports are already taken.

`--compress-responses`  (default True)
: Use gzip to compress responses for clients that indicate they are compatible with it. You may want to turn this off if your server's CPU is more important than your network bandwidth (e.g. browser on same machine).

Logging options
---------------

`--profile`  (default 0)
: Log timing statistics every N seconds (only when not idle)

`--profile-lines`  (default 5)
: Number of lines to log when profile option is in use (not applicable if using --multicore)

`--renderLog`  (default False)
: Whether or not to log requests for character-set renderer images. Note that this can generate a **lot** of log entries on some pages.

`--logUnsupported`  (default False)
: Whether or not to log attempts at requests using unsupported HTTP methods. Note that this can sometimes generate nearly as many log entries as renderLog if some browser (or malware) tries to do WebDAV PROPFIND requests on each of the images.

`--logRedirectFiles`  (default True)
: Whether or not to log requests that result in the browser being simply redirected to the original site when the redirectFiles option is on.

`--ipNoLog` 
: A comma-separated list of IP addresses which can use the adjuster without being logged. If your network has a "friendly probing" service then you might want to use this to stop it filling up the logs.  (Any tracebacks it causes will still be logged however.)

`--squashLogs`  (default True)
: Try to remove some duplicate information from consecutive log entries, to make logs easier to check. You might want to set this to False if you plan to use automatic search tools on the logs. Currently not supported with multicore, and will automatically be set to False if multicore is enabled.

`--errorHTML`  (default Adjuster error has been logged)
: What to say when an uncaught exception (due to a misconfiguration or programming error) has been logged. HTML markup is allowed in this message. If for some reason you have trouble accessing the log files, the traceback can usually be included in the page itself by placing {traceback} in the message.

`--logDebug`  (default False)
: Write debugging messages (to standard error if in the foreground, or to the logs if in the background). Use as an alternative to --logging=debug if you don't also want debug messages from other Tornado modules. On Unix you may also toggle this at runtime by sending SIGUSR1 to the process(es).

Tornado-provided logging options are not listed above because they might vary across Tornado versions; run `python adjuster.py --help` to see a full list of the ones available on your setup. They typically include `log_file_max_size`, `log_file_num_backups`, `log_file_prefix` and `log_to_stderr`.

Using Web Adjuster in WSGI mode
===============================
Web Adjuster is best run as a standalone server (see above) or behind a proxy like `nginx`, but if you must use WSGI then you can do it like this:

1. In your wrapper Python script, `import adjuster`
2. Set options via `adjuster.options.`optionName = value (remembering to set `port` to 80; options are as above, but some of them, such as server control options, do not apply to WSGI mode)
3. Do `myApp = adjuster.make_WSGI_application()`
4. Do something with `myApp`, according to whatever WSGI framework you are using:
## AppEngine
on a Standard second-generation runtime (under Solutions / All products / Serverless / App Engine / Create Application):
1. Make an `app.yaml` file like:

    runtime: python312
    automatic_scaling:
      max_instances: 1
      min_instances: 0

2. Place and/or symlink this `app.yaml` along with `adjuster.py` and your wrapper script, which you should call `main.py` and change `myApp` to `app`, and also copy or symlink the `tornado` subdirectory from a download of Tornado version 5.1.1 or below (this is so AppEngine will run gunicorn for you; version 6 dropped WSGI functionality; alternatively you can directly set up Tornado in non-WSGI mode but this is more difficult on AppEngine Standard). ​You might also need to create an empty "placeholder" version of `fcntl.py` (Tornado 3 also needs an empty `ssl.py` but this shouldn't be done if you downloaded Tornado 5). New deployments after February 2020 add a region code to the URL (e.g. `example.ue.r.appspot.com` for US-East or `example.uc.r.appspot.com` for US-Central); setting this in `host_suffix` and setting `alt_dot="-dot-"` is necessary if you want to use `urlscheme="//"` (even in pre-2020 deployments), but it leads to a bad situation with subdomain cookies as documented in the `alt-dot` option.
3. If your settings need PIL or LXML, add a `requirements.txt` like

        pillow
        lxml

4. Deploy via `gcloud app deploy app.yaml --project` followed by the app ID you registered. ​Since 2020, a payment method must be entered even if you use only the "free tier".  Google said the above setting of `max_instances: 1` "usually keeps your instance hour usage within the free tier" but from 2023 `gcloud app deploy` started to replicate a "bucket" across multiple regions using traffic that's no longer included in Google’s "free tier": it charges about a penny every time you update your app, invoiced as "Networking Traffic Egress GCP Replication within Northern America" and might cause problems later if your billing details are outdated (I've not figured out a way to make AppEngine plus buckets all single region); additionally, over many updates the "artifacts" storage bucket might accumulate enough container images to take you above the free storage quota, incurring small monthly storage charges until you log in to console.cloud.google.com and remove old container images.

Options that call external programs are unlikely to work in AppEngine Standard but you can use htmlFilter with Python functions (see above; if you have large modules not always used then you might want to import these on demand).

## Werkzeug, cherrypy etc
If using Werkzeug, cherrypy.wsgiserver, or similar, do `werkzeug.serving.run_simple(`IP, port`, myApp, threaded=True)` or `cherrypy.wsgiserver.CherryPyWSGIServer((`IP, port`), myApp).start()` or whatever.  You will need Tornado 5.1.1 or below (Tornado 6 doesn’t support this) and it has to be installed properly rather than simply placing its `tornado` subdirectory into the current directory, unless it’s Tornado 2.4.1 on Python 2.6 or 2.7.
## CGI
You can turn it into a CGI script via `import wsgiref.handlers ; wsgiref.handlers.CGIHandler().run(myApp)` but that will need a separate process for each concurrent request. ​Again you will need Tornado 5.1.1 or below (Tornado 6 doesn’t support this), and it has to be installed properly rather than simply placing its tornado subdirectory into the current directory, unless it’s Tornado 2.4.1 on Python 2.6 or 2.7. If using Apache, put

    ErrorDocument 404 /wrapper.cgi
    Options -Indexes
    ErrorDocument 403 /wrapper.cgi

in `.htaccess` (and ensure `AllowOverride All` is set in the config files) to send all requests to the CGI, which should then import adjuster from outside the webspace (e.g. by adding to `sys.path` first), but it’s not necessary to send other requests to the CGI if you set submitPath to the CGI’s path plus `?` and want only the 'enter your own text’ functionality.

Options for Annotator Generator v3.407
======================================

`-h`, `--help`
 : show this help message and exit

`--infile=`
 : Filename of a text file (or a compressed .gz, .bz2 or .xz file or URL) to read the input examples from. If this is not specified, standard input is used.

`--incode=`
 : Character encoding of the input file (default utf-8)

`--mstart=`
 : The string that starts a piece of text with annotation markup in the input examples; default `<ruby><rb>`

`--mmid=`
 : The string that occurs in the middle of a piece of markup in the input examples, with the word on its left and the added markup on its right (or the other way around if mreverse is set); default `</rb><rt>`

`--mend=`
 : The string that ends a piece of annotation markup in the input examples; default `</rt></ruby>`

`-r`, `--mreverse`
 : Specifies that the annotation markup is reversed, so the text **before** mmid is the annotation and the text **after** it is the base text

`--no-mreverse`
 : Cancels any earlier `--mreverse` option in Makefile variables etc

`--end-pri=`
 : Treat words that occur in the examples before this delimeter as having "high priority" for Yarowsky-like seed collocations (if these are in use).  Normally the Yarowsky-like logic tries to identify a "default" annotation based on what is most common in the examples, with the exceptions indicated by collocations.  If however a word is found in a high-priority section at the start, then the first annotation found there will be taken as the ideal "default" even if it's in a minority in the examples; everything else will be taken as an exception.

`-s`, `--spaces`
 : Set this if you are working with a language that uses whitespace in its non-markedup version (not fully tested).  The default is to assume that there will not be any whitespace in the language, which is correct for Chinese and Japanese.

`--no-spaces`
 : Cancels any earlier `--spaces` option in Makefile variables etc

`-c`, `--capitalisation`
 : Don't try to normalise capitalisation in the input.  Normally, to simplify the rules, the analyser will try to remove start-of-sentence capitals in annotations, so that the only remaining words with capital letters are the ones that are **always** capitalised such as names.  (That's not perfect: some words might always be capitalised just because they never occur mid-sentence in the examples.)  If this option is used, the analyser will instead try to "learn" how to predict the capitalisation of **all** words (including start of sentence words) from their contexts.

`--no-capitalisation`
 : Cancels any earlier `--capitalisation` option in Makefile variables etc

`-w`, `--annot-whitespace`
 : Don't try to normalise the use of whitespace and hyphenation in the example annotations.  Normally the analyser will try to do this, to reduce the risk of missing possible rules due to minor typographical variations.

`--no-annot-whitespace`
 : Cancels any earlier `--annot-whitespace` option in Makefile variables etc

`--keep-whitespace=`
 : Comma-separated list of words (without annotation markup) for which whitespace and hyphenation should always be kept even without the `--annot-whitespace` option.  Use when you know the variation is legitimate. This option expects words to be encoded using the system locale (UTF-8 if it cannot be detected).

`--suffix=`
 : Comma-separated list of annotations that can be considered optional suffixes for normalisation

`--suffix-minlen=`
 : Minimum length of word (in Unicode characters) to apply suffix normalisation

`--post-normalise=`
 : Filename or URL of an optional Python module defining a dictionary called 'table' mapping integers to integers for arbitrary single-character normalisation on the Unicode BMP.  This can reduce the size of the annotator.  It is applied in post-processing (does not affect rules generation itself).  For example this can be used to merge the recognition of Full, Simplified and Variant forms of the same Chinese character in cases where this can be done without ambiguity, if it is acceptable for the generated annotator to recognise mixed-script words should they occur.  If any word in the examples has a different annotation when normalised than not, the normalised version takes precedence.

`--glossfile=`
 : Filename of an optional text file (or compressed .gz, .bz2 or .xz file or URL) to read auxiliary "gloss" information.  Each line of this should be of the form: word (tab) annotation (tab) gloss.  Extra tabs in the gloss will be converted to newlines (useful if you want to quote multiple dictionaries).  When the compiled annotator generates ruby markup, it will add the gloss string as a popup title whenever that word is used with that annotation (before any reannotator option is applied).  The annotation field may be left blank to indicate that the gloss will appear for all other annotations of that word.  The entries in glossfile do **not** affect the annotation process itself, so it's not necessary to completely debug glossfile's word segmentation etc.

`-C`, `--gloss-closure=`
 : If any Chinese, Japanese or Korean word is missing from glossfile, search its closure of variant characters also, using the Unihan variants file (or URL) specified by this option

`--no-gloss-closure`
 : Cancels any earlier `--gloss-closure` option in Makefile variables etc

`-M`, `--glossmiss-omit`
 : Omit rules containing any word not mentioned in glossfile.  Might be useful if you want to train on a text that uses proprietary terms and don't want to accidentally 'leak' those terms (assuming they're not accidentally included in glossfile also).  Words may also be listed in glossfile with an empty gloss field to indicate that no gloss is available but rules using this word needn't be omitted.

`--no-glossmiss-omit`
 : Cancels any earlier `--glossmiss-omit` option in Makefile variables etc

`--words-omit=`
 : File (or compressed .gz, .bz2 or .xz file or URL) containing words (one per line, without markup) to omit from the annotator.  Use this to make an annotator smaller if for example if you're working from a rules file that contains long lists of place names you don't need this particular annotator to recognise but you still want to keep them as rules for other annotators, but be careful because any word on such a list gets omitted even if it also has other meanings (some place names are also normal words).

`--manualrules=`
 : Filename of an optional text file (or compressed .gz, .bz2 or .xz file or URL) to read extra, manually-written rules.  Each line of this should be a marked-up phrase (in the input format) which is to be unconditionally added as a rule.  Use this sparingly, because these rules are not taken into account when generating the others and they will be applied regardless of context (although a manual rule might fail to activate if the annotator is part-way through processing a different rule); try checking messages from `--diagnose-manual`.

`--c-filename=`
 : Where to write the C, C#, Python, Javascript, Go or Dart program. Defaults to standard output, or annotator.c in the system temporary directory if standard output seems to be the terminal (the program might be large, especially if Yarowsky-like indicators are not used, so it's best not to use a server home directory where you might have limited quota).

`--c-compiler=`
 : The C compiler to run if generating C and standard output is not connected to a pipe. The default is to use the "cc" command which usually redirects to your "normal" compiler. You can add options (remembering to enclose this whole parameter in quotes if it contains spaces), but if the C program is large then adding optimisation options may make the compile take a **long** time. If standard output is connected to a pipe, then this option is ignored because the C code will simply be written to the pipe. You can also set this option to an empty string to skip compilation. Default: cc -o annotator

`--outcode=`
 : Character encoding to use in the generated parser (default utf-8, must be ASCII-compatible i.e. not utf-16)

`--rulesFile=`
 : Filename of a JSON file to hold the accumulated rules. Adding .gz, .bz2 or .xz for compression is acceptable. If this is set then either `--write-rules` or `--read-rules` must be specified.

`--write-rules`
 : Write rulesFile instead of generating a parser.  You will then need to rerun with `--read-rules` later.

`--no-write-rules`
 : Cancels any earlier `--write-rules` option in Makefile variables etc

`--read-rules`
 : Read rulesFile from a previous run, and apply the output options to it. You should still specify the input formatting options (which should not change), and any glossfile or manualrules options (which may change), but no input is required.

`--no-read-rules`
 : Cancels any earlier `--read-rules` option in Makefile variables etc

`-E`, `--newlines-reset`
 : Have the annotator reset its state on every newline byte. By default newlines do not affect state such as whether a space is required before the next word, so that if the annotator is used with Web Adjuster's htmlText option (which defaults to using newline separators) the spacing should be handled sensibly when there is HTML markup in mid-sentence.

`--no-newlines-reset`
 : Cancels any earlier `--newlines-reset` option in Makefile variables etc

`-z`, `--compress`
 : Compress annotation strings in the C code.  This compression is designed for fast on-the-fly decoding, so it saves only a limited amount of space (typically 10-20%) but might help if RAM is short.

`--no-compress`
 : Cancels any earlier `--compress` option in Makefile variables etc

`-Z`, `--zlib`
 : Compress the embedded data table using zlib (or pyzopfli if available), and include code to call zlib to decompress it on load.  Useful if the runtime machine has the zlib library and you need to save disk space but not RAM (the decompressed table is stored separately in RAM, unlike `--compress` which, although giving less compression, at least works 'in place').  Once `--zlib` is in use, specifying `--compress` too will typically give an additional disk space saving of less than 1% (and a runtime RAM saving that's greater but more than offset by zlib's extraction RAM).  If generating a Javascript annotator with zlib, the decompression code is inlined so there's no runtime zlib dependency, but startup can be ~50% slower so this option is not recommended in situations where the annotator is frequently reloaded from source (unless you're running on Node.js in which case loading is faster due to the use of Node's "Buffer" class).

`--no-zlib`
 : Cancels any earlier `--zlib` option in Makefile variables etc

`-l`, `--library`
 : Instead of generating C code that reads and writes standard input/output, generate a C library suitable for loading into Python via ctypes.  This can be used for example to preload a filter into Web Adjuster to cut process-startup delays.

`--no-library`
 : Cancels any earlier `--library` option in Makefile variables etc

`-W`, `--windows-clipboard`
 : Include C code to read the clipboard on Windows or Windows Mobile and to write an annotated HTML file and launch a browser, instead of using the default cross-platform command-line C wrapper.  See the start of the generated C file for instructions on how to compile for Windows or Windows Mobile.

`--no-windows-clipboard`
 : Cancels any earlier `--windows-clipboard` option in Makefile variables etc

`--java=`
 : Instead of generating C code, generate Java, and place the *.java files in the directory specified by this option.  The last part of the directory should be made up of the package name; a double slash (//) should separate the rest of the path from the package name, e.g. `--java`=/path/to/wherever//org/example/annotator and the main class will be called Annotator.

`--android=`
 : URL for an Android app to browse (`--java` must be set).  If this is set, code is generated for an Android app which starts a browser with that URL as the start page, and annotates the text on every page it loads.  Use file:///android_asset/index.html for local HTML files in the assets directory; a clipboard viewer is placed in clipboard.html, and the app will also be able to handle shared text.  If certain environment variables are set, this option can also compile and sign the app using Android SDK command-line tools (otherwise it puts a message on stderr explaining what needs to be set)

`--android-template=`
 : File (or URL) to use as a template for Android start HTML.  This option implies `--android`=file:///android_asset/index.html and generates that index.html from the file specified (or from a built-in default if the special filename 'blank' is used).  The template file may include URL_BOX_GOES_HERE to show a URL entry box and related items (offline-clipboard link etc) in the page, in which case you can optionally define a Javascript function 'annotUrlTrans' to pre-convert some URLs from shortcuts etc; also enables better zoom controls on Android 4+, a mode selector if you use `--annotation-names`, a selection scope control on recent-enough WebKit, and a visible version stamp (which, if the device is in 'developer mode', you may double-tap on to show missing glosses). VERSION_GOES_HERE may also be included if you want to put it somewhere other than at the bottom of the page. If you do include URL_BOX_GOES_HERE you'll have an annotating Web browser app that allows the user to navigate to arbitrary URLs: as of 2020, this is acceptable on Google Play and Huawei AppGallery (non-China only from 2022), but **not** Amazon AppStore as they don't want 'competition' to their Silk browser.

`--gloss-simplify=`
 : A regular expression matching parts of glosses to remove when generating a '3-line' format in apps, but not for hover titles or popups.  Default removes parenthesised expressions if not solitary, anything after the first slash or semicolon, and the leading word 'to'.  Can be set to empty string to omit simplification.

`-L`, `--pleco-hanping`
 : In the Android app, make popup definitions link to Pleco or Hanping if installed

`--no-pleco-hanping`
 : Cancels any earlier `--pleco-hanping` option in Makefile variables etc

`--bookmarks=`
 : Android bookmarks: comma-separated list of package names that share our bookmarks. If this is not specified, the browser will not be given a bookmarks function. If it is set to the same value as the package specified in `--java`, bookmarks are kept in just this Android app. If it is set to a comma-separated list of packages that have also been generated by annogen (presumably with different annotation types), and if each one has the same android:sharedUserId attribute in AndroidManifest.xml's 'manifest' tag (you'll need to add this manually), and if the same certificate is used to sign all of them, then bookmarks can be shared across the set of browser apps.  But beware the following two issues: (1) adding an android:sharedUserId attribute to an app that has already been released without one causes some devices to refuse the update with a 'cannot install' message (details via adb logcat; affected users would need to uninstall and reinstall instead of update, and some of them may not notice the instruction to do so); (2) this has not been tested with Google's new "App Bundle" arrangement, and may be broken if the Bundle results in APKs being signed by a different key.  In June 2019 Play Console started issuing warnings if you release an APK instead of a Bundle, even though the "size savings" they mention are under 1% for annogen-generated apps.

`-e`, `--epub`
 : When generating an Android browser, make it also respond to requests to open EPUB files. This results in an app that requests the 'read external storage' permission on Android versions below 6, so if you have already released a version without EPUB support then devices running Android 5.x or below will not auto-update past this change until the user notices the update notification and approves the extra permission.

`--no-epub`
 : Cancels any earlier `--epub` option in Makefile variables etc

`--android-print`
 : When generating an Android browser, include code to provide a Print option (usually print to PDF) and a simple highlight-selection option. The Print option will require Android 4.4, but the app should still run without it on earlier versions of Android.

`--no-android-print`
 : Cancels any earlier `--android-print` option in Makefile variables etc

`--known-characters=`
 : When generating an Android browser, include an option to leave the most frequent characters unannotated as 'known'.  This option should be set to the filename or URL of a UTF-8 file of characters separated by newlines, assumed to be most frequent first, with characters on the same line being variants of each other (see `--freq-count` for one way to generate it). Words consisting entirely of characters found in the first N lines of this file (where N is settable by the user) will be unannotated until tapped on.

`--freq-count=`
 : Name of a file to write that is suitable for the known-characters option, taken from the input examples (which should be representative of typical use).  Any post-normalise table provided will be used to determine which characters are equivalent.

`--android-audio=`
 : When generating an Android browser, include an option to convert the selection to audio using this URL as a prefix, e.g. https://example.org/speak.cgi?text= (use for languages not likely to be supported by the device itself). Optionally follow the URL with a space (quote carefully) and a maximum number of words to read in each user request. Setting a limit is recommended, or somebody somewhere will likely try 'Select All' on a whole book or something and create load problems. You should set a limit server-side too of course.

`--extra-js=`
 : Extra Javascript to inject into sites to fix things in the Android browser app. The snippet will be run before each scan for new text to annotate. You may also specify a file to read: `--extra-js`=@file.js or `--extra-js`=@file1.js,file2.js (or URLs; do not use // comments in these files, only /* ... */ because newlines will be replaced), and you can create variants of the files by adding search-replace strings: `--extra-js`=@file1.js:search:replace,file2.js

`--tts-js`
 : Make Android 5+ multilingual Text-To-Speech functions available to extra-js scripts (see TTSInfo code for details)

`--no-tts-js`
 : Cancels any earlier `--tts-js` option in Makefile variables etc

`--existing-ruby-js-fixes=`
 : Extra Javascript to run in the Android browser app or browser extension whenever existing RUBY elements are encountered; the DOM node above these elements will be in the variable n, which your code can manipulate or replace to fix known problems with sites' existing ruby (such as common two-syllable words being split when they shouldn't be). Use with caution. You may also specify a file or URL to read: `--existing-ruby-js-fixes`=@file.js

`--existing-ruby-lang-regex=`
 : Set the Android app or browser extension to remove existing ruby elements unless the document language matches this regular expression. If `--sharp-multi` is in use, you can separate multiple regexes with comma and any unset will always delete existing ruby.  If this option is not set at all then existing ruby is always kept.

`--existing-ruby-shortcut-yarowsky`
 : Set the Android browser app to 'shortcut' Yarowsky-like collocation decisions when adding glosses to existing ruby over 2 or more characters, so that words normally requiring context to be found are more likely to be found without context (this may be needed because adding glosses to existing ruby is done without regard to context)

`--extra-css=`
 : Extra CSS to inject into sites to fix things in the Android browser app. You may also specify a file or URL to read `--extra-css`=@file.css

`--app-name=`
 : User-visible name of the Android app

`--compile-only`
 : Assume the code has already been generated by a previous run, and just run the compiler

`--no-compile-only`
 : Cancels any earlier `--compile-only` option in Makefile variables etc

`-j`, `--javascript`
 : Instead of generating C code, generate JavaScript.  This might be useful if you want to run an annotator on a device that has a JS interpreter but doesn't let you run your own binaries.  The JS will be table-driven to make it load faster.  See comments at the start for usage.

`--no-javascript`
 : Cancels any earlier `--javascript` option in Makefile variables etc

`-6`, `--js-6bit`
 : When generating a Javascript annotator, use a 6-bit format for many addresses to reduce escape codes in the data string by making more of it ASCII

`--no-js-6bit`
 : Cancels any earlier `--js-`6bit option in Makefile variables etc

`-8`, `--js-octal`
 : When generating a Javascript annotator, use octal instead of hexadecimal codes in the data string when doing so would save space. This does not comply with ECMAScript 5 and may give errors in its strict mode.

`--no-js-octal`
 : Cancels any earlier `--js-octal` option in Makefile variables etc

`-9`, `--ignore-ie8`
 : When generating a Javascript annotator, do not make it backward-compatible with Microsoft Internet Explorer 8 and below. This may save a few bytes.

`--no-ignore-ie8`
 : Cancels any earlier `--ignore-ie`8 option in Makefile variables etc

`-u`, `--js-utf8`
 : When generating a Javascript annotator, assume the script can use UTF-8 encoding directly and not via escape sequences. In some browsers this might work only on UTF-8 websites, and/or if your annotation can be expressed without the use of Unicode combining characters.

`--no-js-utf8`
 : Cancels any earlier `--js-utf`8 option in Makefile variables etc

`--browser-extension=`
 : Name of a Chrome or Firefox browser extension to generate.  The extension will be placed in a directory of the same name (without spaces), which may optionally already exist and contain icons like 32.png and 48.png to be used.

`--browser-extension-description=`
 : Description field to use when generating browser extensions

`--manifest-v3`
 : Use Manifest v3 instead of Manifest v2 when generating browser extensions (tested on Chrome only, and requires Chrome 88 or higher).  This is now required for all Chrome Web Store uploads.

`--gecko-id=`
 : a Gecko (Firefox) ID to embed in the browser extension

`--dart`
 : Instead of generating C code, generate Dart.  This might be useful if you want to run an annotator in a Flutter application.

`--no-dart`
 : Cancels any earlier `--dart` option in Makefile variables etc

`--dart-datafile=`
 : When generating Dart code, put annotator data into a separate file and open it using this pathname. Not compatible with Dart's "Web app" option, but might save space in a Flutter app (especially along with `--zlib`)

`-Y`, `--python`
 : Instead of generating C code, generate a Python module.  Similar to the Javascript option, this is for when you can't run your own binaries, and it is table-driven for fast loading.

`--no-python`
 : Cancels any earlier `--python` option in Makefile variables etc

`--reannotator=`
 : Shell command through which to pipe each word of the original text to obtain new annotation for that word.  This might be useful as a quick way of generating a new annotator (e.g. for a different topolect) while keeping the information about word separation and/or glosses from the previous annotator, but it is limited to commands that don't need to look beyond the boundaries of each word.  If the command is prefixed by a # character, it will be given the word's existing annotation instead of its original text, and if prefixed by ## it will be given text#annotation.  The command should treat each line of its input independently, and both its input and its output should be in the encoding specified by `--outcode`.

`-A`, `--reannotate-caps`
 : When using `--reannotator`, make sure to capitalise any word it returns that began with a capital on input

`--no-reannotate-caps`
 : Cancels any earlier `--reannotate-caps` option in Makefile variables etc

`--sharp-multi`
 : Assume annotation (or reannotator output) contains multiple alternatives separated by # (e.g. pinyin#Yale) and include code to select one by number at runtime (starting from 0). This is to save on total space when shipping multiple annotators that share the same word grouping and gloss data, differing only in the transcription of each word.

`--no-sharp-multi`
 : Cancels any earlier `--sharp-multi` option in Makefile variables etc

`--annotation-names=`
 : Comma-separated list of annotation types supplied to sharp-multi (e.g. Pinyin,Yale), if you want the Android app etc to be able to name them.  You can also set just one annotation names here if you are not using sharp-multi.

`--annotation-map=`
 : Comma-separated list of annotation-number overrides for sharp-multi, e.g. 7=3 to take the 3rd item if a 7th is selected

`--annotation-postprocess=`
 : Extra code for post-processing specific annotNo selections after retrieving from a sharp-multi list (@file or @url allowed)

`-o`, `--allow-overlaps`
 : Normally, the analyser avoids generating rules that could overlap with each other in a way that would leave the program not knowing which one to apply.  If a short rule would cause overlaps, the analyser will prefer to generate a longer rule that uses more context, and if even the entire phrase cannot be made into a rule without causing overlaps then the analyser will give up on trying to cover that phrase.  This option allows the analyser to generate rules that could overlap, as long as none of the overlaps would cause actual problems in the example phrases. Thus more of the examples can be covered, at the expense of a higher risk of ambiguity problems when applying the rules to other texts.  See also the -y option.

`--no-allow-overlaps`
 : Cancels any earlier `--allow-overlaps` option in Makefile variables etc

`-y`, `--ybytes=`
 : Look for candidate Yarowsky seed-collocations within this number of bytes of the end of a word.  If this is set then overlaps and rule conflicts will be allowed when seed collocations can be used to distinguish between them, and the analysis is likely to be faster.  Markup examples that are completely separate (e.g. sentences from different sources) must have at least this number of (non-whitespace) bytes between them.

`--ybytes-max=`
 : Extend the Yarowsky seed-collocation search to check over larger ranges up to this maximum.  If this is set then several ranges will be checked in an attempt to determine the best one for each word, but see also ymax-threshold and ymax-limitwords.

`--ymax-threshold=`
 : Limits the length of word that receives the narrower-range Yarowsky search when ybytes-max is in use. For words longer than this, the search will go directly to ybytes-max. This is for languages where the likelihood of a word's annotation being influenced by its immediate neighbours more than its distant collocations increases for shorter words, and less is to be gained by comparing different ranges when processing longer words. Setting this to 0 means no limit, i.e. the full range will be explored on **all** Yarowsky checks.

`--ymax-limitwords=`
 : Comma-separated list of words (without annotation markup) for which the ybytes expansion loop should run at most two iterations.  This may be useful to reduce compile times for very common ambiguous words that depend only on their immediate neighbours.  Annogen may suggest words for this option if it finds they take inordinate time to process.

`--ybytes-step=`
 : The increment value for the loop between ybytes and ybytes-max

`-k`, `--warn-yarowsky`
 : Warn when absolutely no distinguishing Yarowsky seed collocations can be found for a word in the examples

`--no-warn-yarowsky`
 : Cancels any earlier `--warn-yarowsky` option in Makefile variables etc

`-K`, `--yarowsky-all`
 : Accept Yarowsky seed collocations even from input characters that never occur in annotated words (this might include punctuation and example-separation markup)

`--no-yarowsky-all`
 : Cancels any earlier `--yarowsky-all` option in Makefile variables etc

`--yarowsky-multiword`
 : Check potential multiword rules for Yarowsky seed collocations also.  Without this option (default), only single-word rules are checked.

`--no-yarowsky-multiword`
 : Cancels any earlier `--yarowsky-multiword` option in Makefile variables etc

`--yarowsky-thorough`
 : Recheck Yarowsky seed collocations when checking if any multiword rule would be needed to reproduce the examples.  This could risk 'overfitting' the example set.

`--no-yarowsky-thorough`
 : Cancels any earlier `--yarowsky-thorough` option in Makefile variables etc

`--yarowsky-half-thorough`
 : Like `--yarowsky-thorough` but check only what collocations occur within the proposed new rule (not around it), less likely to overfit

`--no-yarowsky-half-thorough`
 : Cancels any earlier `--yarowsky-half-thorough` option in Makefile variables etc

`--yarowsky-debug=`
 : Report the details of seed-collocation false positives if there are a large number of matches and at most this number of false positives (default 1). Occasionally these might be due to typos in the corpus, so it might be worth a check.

`--allow-exceptions=`
 : Filename (or URL) of any known exeptions for `--yarowsky-debug` checks (default allow-exceptions.txt)

`--normalise-debug=`
 : When `--capitalisation` is not in effect. report words that are usually capitalised but that have at most this number of lower-case exceptions (default 1) for investigation of possible typos in the corpus

`--allow-caps-exceptions=`
 : Filename (or URL) of any known exeptions for `--normalise-debug` checks (default allow-caps-exceptions.txt)

`--debug-dir=`
 : Directory in which to write reports of possible typos etc (defaults to current directory)

`--normalise-cache=`
 : Optional file to use to cache the result of normalisation. Adding .gz, .bz2 or .xz for compression is acceptable.

`-1`, `--single-words`
 : Do not generate any rule longer than 1 word, although it can still have Yarowsky seed collocations if -y is set. This speeds up the search, but at the expense of thoroughness. You might want to use this in conjuction with -y to make a parser quickly.

`--no-single-words`
 : Cancels any earlier `--single-words` option in Makefile variables etc

`--max-words=`
 : Limits the number of words in a rule.  0 means no limit.  `--single-words` is equivalent to `--max-words`=1.  If you need to limit the search time, and are using -y, it should suffice to use `--single-words` for a quick annotator or `--max-words`=5 for a more thorough one (or try 3 if `--yarowsky-half-thorough` is in use).

`--multiword-end-avoid=`
 : Comma-separated list of words (without annotation markup) that should be avoided at the end of a multiword rule (e.g. sandhi likely to depend on the following word)

`-d`, `--diagnose=`
 : Output some diagnostics for the specified word. Use this option to help answer "why doesn't it have a rule for...?" issues. This option expects the word without markup and uses the system locale (UTF-8 if it cannot be detected).

`--diagnose-limit=`
 : Maximum number of phrases to print diagnostics for (0 means unlimited). Default: 10

`-m`, `--diagnose-manual`
 : Check and diagnose potential failures of `--manualrules`

`--no-diagnose-manual`
 : Cancels any earlier `--diagnose-manual` option in Makefile variables etc

`-q`, `--diagnose-quick`
 : Ignore all phrases that do not contain the word specified by the `--diagnose` option, for getting a faster (but possibly less accurate) diagnostic.  The generated annotator is not likely to be useful when this option is present.

`--no-diagnose-quick`
 : Cancels any earlier `--diagnose-quick` option in Makefile variables etc

`--priority-list=`
 : Instead of generating an annotator, use the input examples to generate a list of (non-annotated) words with priority numbers, a higher number meaning the word should have greater preferential treatment in ambiguities, and write it to this file (or compressed .gz, .bz2 or .xz file).  If the file provided already exists, it will be updated, thus you can amend an existing usage-frequency list or similar (although the final numbers are priorities and might no longer match usage-frequency exactly).  The purpose of this option is to help if you have an existing word-priority-based text segmenter and wish to update its data from the examples; this approach might not be as good as the Yarowsky-like one (especially when the same word has multiple readings to choose from), but when there are integration issues with existing code you might at least be able to improve its word-priority data.

`-t`, `--time-estimate`
 : Estimate time to completion.  The code to do this is unreliable and is prone to underestimate.  If you turn it on, its estimate is displayed at the end of the status line as days, hours or minutes.

`--no-time-estimate`
 : Cancels any earlier `--time-estimate` option in Makefile variables etc

`-0`, `--single-core`
 : Use only one CPU core even when others are available on Unix

`--no-single-core`
 : Cancels any earlier `--single-core` option in Makefile variables etc

`--cores-command=`
 : Command to run when changing the number of CPU cores in use (with new number as a parameter); this can run a script to pause/resume any lower-priority load

`-p`, `--status-prefix=`
 : Label to add at the start of the status line, for use if you batch-run annogen in multiple configurations and want to know which one is currently running


Copyright and Trademarks
========================

(c) Silas S. Brown, licensed under Apache 2

* Android is a trademark of Google LLC.

* Apache is a registered trademark of The Apache Software Foundation.

* AppEngine is possibly a trademark of Google LLC.

* Apple is a trademark of Apple Inc.

* Firefox is a registered trademark of The Mozilla Foundation.

* Google Play is a trademark of Google LLC.

* Google is a trademark of Google LLC.

* Java is a registered trademark of Oracle Corporation in the US and possibly other countries.

* Javascript is a trademark of Oracle Corporation in the US.

* Linux is the registered trademark of Linus Torvalds in the U.S. and other countries.

* MP3 is a trademark that was registered in Europe to Hypermedia GmbH Webcasting but I was unable to confirm its current holder.

* Mac is a trademark of Apple Inc.

* Microsoft is a registered trademark of Microsoft Corp.

* Python is a trademark of the Python Software Foundation.

* Raspberry Pi is a trademark of the Raspberry Pi Foundation.

* Unicode is a registered trademark of Unicode, Inc. in the United States and other countries.

* Windows is a registered trademark of Microsoft Corp.

* iPhone is a trademark of Apple in some countries.

* Any other trademarks I mentioned without realising are trademarks of their respective holders.
