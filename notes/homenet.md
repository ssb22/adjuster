
from https://ssb22.user.srcf.net/adjuster/homenet.html (also [mirrored on GitLab Pages](https://ssb22.gitlab.io/adjuster/homenet.html) just in case)

# homenet.org is down

The hobbyist domain `homenet.org` went down on Saturday 29<sup>th</sup> July 2017.

Users of my old service there may wish to try `access.ucam.org` with the part after the `/` being the same as before.

I ran that service from one of Homenet’s 105 subdomains because:
1. the Homenet domain was obviously unofficial (“home networking”)—I wanted to run a mirror of a larger site but with added language-learning helps, and I wanted it to be *as obvious as possible* that mine was an *unofficial* mirror;
2. the domain was still short and memorable—to protect the original site’s reputation, I wanted to prevent search engines from seeing my version, and spread it only via word of mouth to those I *knew* would understand—so I needed a link people can remember easily so they wouldn’t have to search;
3. it didn’t have my name on it—I was still traceable for legal purposes, but I didn’t want anyone to think I was trying to take credit away from the original site.

Nevertheless I did **not** control Homenet at top level (they only gave me a subdomain), so when the proprietor of Homenet pulled the plug, I was gone. That’s the risk of hobbyist service providers. It was **not** a result of anything that happened between me and the original site.

(At the original site’s request I had already suspended my full mirroring service at the end of 2013, but I continued to maintain specialised indexes and dictionaries for language-learning use which extensively linked to that site, plus custom browser extensions and phone applications for the same purpose; all of these continued to be available from my Homenet subdomain. The 2017 demise of that subdomain was due **only** to the upstream demise of Homenet as a service provider; there’s no need to speculate anything else.)

I did attempt to contact the owner of Homenet to ask if they needed help with maintenance, but I didn’t receive a reply.

After 6 weeks of downtime, the domain **expired** on 10<sup>th</sup> September 2017, and the hobbyist’s registrar did not automatically renew it as some do. Instead the expiring domain was automatically bought by a company called DropCatch, which sold it at auction for 2,060 US dollars to Oleksandr Protoven of Kiev (bidding as “capito” and reportedly already holding 125+ domains mostly redirecting to hotel directories); 6 weeks later Homenet was pointed to a list of “hotels in Vienna” and I don’t think they’d appreciate users of Homenet’s old hobby subdomains asking for redirects. (In 2025 they changed the configuration so that the old subdomains just said “not found” while only the main domain redirected to the hotels in Vienna.)

## Bookmarklet service

Some of the ‘bookmarklet’ browser extensions I was serving from my old Homenet address continued to function for a while, because they used an `rhcloud.com` address for ‘back-end’ processing (I couldn’t go via `homenet.org` for that, due to SSL certification issues). This `rhcloud.com` address pointed to a virtual server in the “Openshift Online 2” system, which Red Hat said they’d shut down on Saturday 30<sup>th</sup> September 2017 (actually they took it offline in the early hours of Tuesday 3<sup>rd</sup> October, then at 10:45pm gave us a temporary reprieve saying last chance to back up until 5pm Thursday and took it offline again at 11:24pm Thursday 5<sup>th</sup>). They told us to upgrade to Openshift Online 3, but that would have broken the bookmarklets *anyway* (`rhcloud.com` addresses were being changed into `openshiftapps.com` addresses and there was no clear way to keep an existing address), so there was no good reason to go through with the hassle plus the (relatively high) financial cost of keeping an Online 3 instance up 24/7—as I was going to lose the address anyway, leaving Openshift became the best of the remaining options.

The Openshift shutdown was not related to the Homenet shutdown, but they happened to occur close to each other and the answer to both is for everybody to change to using `access.ucam.org` addresses. But I never had a list of my users, so I couldn’t tell them. This page is here in the hope that some of them might find it via search.

Copyright and Trademarks:
All material © Silas S. Brown unless otherwise stated.
Openshift is a registered trademark of Red Hat Inc.
Red Hat is a registered trademark of Red Hat Inc.
Any other [trademarks](https://ssb22.user.srcf.net/trademarks.html) I mentioned without realising are trademarks of their respective holders.
