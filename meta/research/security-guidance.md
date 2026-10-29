# Current standards guidance: IPv6/IPv4 address text, IPv4-mapped, POSIX.1-2024 sockets — research digest

**As of 2026-10-29.** Security digest: stale after 2027-01-27 (90 days), and re-run at the hardening cycle. Question: what do the standards bodies currently specify for the surfaces the library's rules rest on: the IPv6 addressing architecture and text form (RFC 4291 and RFC 5952, and anything updating them), IPv4 dotted-quad strictness (POSIX `inet_pton`, IETF guidance on octal and short forms), IPv4-mapped IPv6 addresses, and POSIX's socket interfaces (`MSG_NOSIGNAL`, `SOCK_NONBLOCK`/`SOCK_CLOEXEC`, `accept4`) in POSIX.1-2024 (Issue 8)? (Request 2 of 3, nitpick-sockets meta/roadmap/0.0/0.0.0.md §13 at af50100.)

## Answer

RFC 4291 (February 2006, status Draft Standard) is still the IPv6 addressing architecture. The RFC Editor returned no "Obsoleted By" field for it and lists six updaters (RFC 5952, 6052, 7136, 7346, 7371, 8064, the highest-numbered being 8064). POSIX.1-2024 still points to it for the IPv6 text forms. RFC 5952 (August 2010, Standards Track, "Updates: 4291") is the text-form update.

- **Generating text, per RFC 5952:**
  - Leading zeros are suppressed and hex is lower case.
  - "::" is used to its maximum but never for a single 16-bit zero field.
  - The longest zero run is shortened (the first on a tie).
  - A mapped address is written ::ffff:a.b.c.d.
- **Parsing, per RFC 5952:** all implementations MUST accept any legitimate RFC 4291 format.
- **Not confirmed:** RFC 5952's own status page returned HTTP 502, so its currency is unconfirmed. Of the six updaters only RFC 5952 was read.

IPv4 dotted-quad text:
- POSIX.1-2024 `inet_pton` takes each "ddd" as a one to three digit decimal number from 0 to 255.
- It says "Leading zeros shall be allowed" (Austin Group Defect 1573, Issue 8).
- It does not accept octal, hexadecimal or fewer-than-four-number forms.
- The IETF's RFC 3986 §3.2.2 grammar admits only four dec-octets, none with a leading zero, and says "only the dotted-decimal form of four octets is allowed by this grammar".
- So the two bodies agree on refusing octal, hex and short forms, and disagree on leading zeros.

IPv4-mapped IPv6:
- An IPv4-mapped IPv6 address (RFC 4291 §2.5.5.2: 80 zero bits, 16 one bits, then the IPv4 address) is a distinct IPv6 address type.
- IPv4-compatible addresses (§2.5.5.1) are deprecated.
- Nothing read requires or forbids a library to convert between the IPv4 and mapped forms.
- The Linux inet_pton(3) page says a mapped address must be supplied explicitly.

POSIX.1-2024 (IEEE Std 1003.1-2024, Issue 8) socket interfaces:
- It specifies accept4(), SOCK_NONBLOCK, SOCK_CLOEXEC and SOCK_CLOFORK. All were added in Issue 8, for socket(), socketpair() and accept4().
- It specifies MSG_NOSIGNAL, which has been in POSIX since 2008 per the Linux man page.
- Linux man-pages 6.19 agrees on what they do (accept4 since Linux 2.6.28 and glibc 2.10; MSG_NOSIGNAL since Linux 2.2).
- There is one documented difference, plain accept(). POSIX leaves O_NONBLOCK inheritance implementation-defined; Linux does not inherit it.
- For SO_REUSEADDR, POSIX.1-2024's `<sys/socket.h>` says only "Reuse of local addresses is supported."; Linux's socket(7) states the behaviour. SO_REUSEPORT is Linux (since 3.9) and is absent from that POSIX page.

## Evidence

**IPv6 architecture and text form**
- <https://www.rfc-editor.org/info/rfc4291> — retrieved 2026-10-29 — "RFC 4291: IP Version 6 Addressing Architecture"; status "Draft Standard"; "February 2006"; "Obsoletes: 3513"; Updated By "RFC 5952", "RFC 6052", "RFC 7136", "RFC 7346", "RFC 7371", "RFC 8064"; no Obsoleted By field was returned; the footer reads "Errata   13 Participate." (whether 13 is an errata count was not established).
- <https://www.rfc-editor.org/rfc/rfc4291.html> — retrieved 2026-10-29 — §2.2:
  - "The preferred form is x:x:x:x:x:x:x:x, where the 'x's are one to four hexadecimal digits of the eight 16-bit pieces of the address."
  - "Note that it is not necessary to write the leading zeros in an individual field"
  - "but there must be at least one numeral in every field (except for the case described in 2.)."
  - "The "::" can only appear once in an address."
  - "The "::" can also be used to compress leading or trailing zeros in an address."
  - "x:x:x:x:x:x:d.d.d.d, where the 'x's are the hexadecimal values of the six high-order 16-bit pieces of the address," and "and the 'd's are the decimal values of the four low-order 8-bit pieces of the address (standard IPv4 representation)."
  - No rule on the letter case of hex digits was found in §2.2; its examples are upper case (for example "ABCD:EF01:2345:6789:ABCD:EF01:2345:6789").
- <https://www.rfc-editor.org/rfc/rfc5952.html> — retrieved 2026-10-29 — header "Updates: 4291", "August 2010", "This is an Internet Standards Track document."
  - Abstract: "It is expected that the canonical format will be followed by humans and systems when representing IPv6 addresses as text, but all implementations must accept and be able to handle any legitimate" (the fetch reports the sentence ends "RFC 4291 format"); "It does not define a format for internal storage, such as within an application or database."
  - §4: "The recommendation in this section SHOULD be followed by systems when generating an address to be represented as text, but all implementations MUST accept and be able to handle any legitimate" (again ending "RFC 4291 format").
  - §4.1: "Leading zeros MUST be suppressed." and "A single 16-bit 0000 field MUST be represented as 0."
  - §4.2.1: "The use of the symbol "::" MUST be used to its maximum capability."
  - §4.2.2: "The symbol "::" MUST NOT be used to shorten just one 16-bit 0 field."
  - §4.2.3: "the longest run of consecutive 16-bit 0 fields MUST be shortened" and "the first sequence of zero bits MUST be shortened."
  - §4.3: "The characters "a", "b", "c", "d", "e", and "f" in an IPv6 address MUST be represented in lowercase."
  - §6: "The [] style as expressed in [RFC3986] SHOULD be employed, and is the default unless otherwise specified." and "For URIs containing IPv6 address literals, [RFC3986] MUST be followed, as well as the rules defined in this document."
  - Security Considerations: "The example on Section 3.2.5 is one that may cause a security risk if used for access control." (this is about comparing addresses as text)

**IPv4-mapped IPv6**
- <https://www.rfc-editor.org/rfc/rfc4291.html> — retrieved 2026-10-29 —
  - §2.5.5.2: "This address type is used to represent the addresses of IPv4 nodes as IPv6 addresses."
  - Layout, as the fetch reports the diagram: 80 bits of zeros, 16 bits FFFF, then the 32-bit IPv4 address.
  - "See [RFC4038] for background on the usage of the "IPv4-mapped IPv6 address"."
  - §2.5.5.1: "The "IPv4-Compatible IPv6 address" is now deprecated because the current IPv6 transition mechanisms no longer use these addresses." and "New or updated implementations are not required to support this address type."
- <https://www.rfc-editor.org/rfc/rfc5952.html> — retrieved 2026-10-29 — §5:
  - "The decimal notation may be used only for the last 32 bits of the address."
  - Mixed notation is "RECOMMENDED if the following condition is met: the address can be distinguished as having IPv4 addresses embedded in the lower 32 bits solely from the address field through the use of a well-known prefix."
  - "The text representation method noted in Section 4 should be applied for the leading hexadecimal part (i.e., ::ffff:192.0.2.1 instead of 0:0:0:0:0:ffff:192.0.2.1)."
  - The fetch summarised the rest of §5 rather than quoting it.

**IPv4 dotted quad**
- <https://pubs.opengroup.org/onlinepubs/9799919799/functions/inet_ntop.html> — retrieved 2026-10-29 — page identifies as "The Open Group Base Specifications Issue 8", "IEEE Std 1003.1-2024".
  - "If the af argument of inet_pton() is AF_INET, the src string shall be in the standard IPv4 dotted-decimal form:" then "ddd.ddd.ddd.ddd" "where "ddd" is a one to three digit decimal number between 0 and 255. Leading zeros shall be allowed."
  - "The inet_pton() function does not accept other formats (such as the octal numbers, hexadecimal numbers, and fewer than four numbers" (ending "that inet_addr() accepts).")
  - Issue 8 change history: "Austin Group Defect 1573 is applied, clarifying that leading zeros are allowed in the IPv4 dotted-decimal form accepted by inet_pton()." and "Austin Group Defect 1685 is applied, updating RFC references."
  - AF_INET6 forms: "The preferred form is "x:x:x:x:x:x:x:x", where the 'x's are the hexadecimal values of the eight 16-bit pieces of the address."; "The "::" can only appear once in an address."; "x:x:x:x:x:x:d.d.d.d". Note: "A more extensive description of the standard representations of IPv6 addresses can be found in RFC 4291." (no section number)
  - RETURN VALUE: "It shall return 0 if the input is not a valid IPv4 dotted-decimal string or a valid IPv6 address string".
  - inet_ntop(): the page does not specify the AF_INET6 output form and does not mention RFC 5952 or mapped/compatible forms.
- <https://www.rfc-editor.org/rfc/rfc3986.html> — retrieved 2026-10-29 — "STD: 66"; "IPv4address = dec-octet "." dec-octet "." dec-octet "." dec-octet" with dec-octet alternatives "DIGIT", "%x31-39 DIGIT", ""1" 2DIGIT", ""2" %x30-34 DIGIT", ""25" %x30-35". A multi-digit dec-octet therefore cannot start with 0 (derived from the ABNF). "Note that other forms of dotted notation may be interpreted on some platforms, as described in Section 7.4," "but only the dotted-decimal form of four octets is allowed by this grammar." Only characters 0 to 100000 of 152435 were read, so §7.4 is unread.
- <https://man7.org/linux/man-pages/man3/inet_pton.3.html> — retrieved 2026-10-29 — "Linux man-pages 6.19" (tarball man-pages-6.19.tar.gz).
  - AF_INET: "_ddd_ is a decimal number of up to three digits in the range 0 to 255." The page is silent on leading zeros.
  - VERSIONS: inet_pton() "accepts only IPv4 addresses in dotted-decimal notation, whereas inet_aton(3) and inet_addr(3) allow the more general numbers-and-dots notation (hexadecimal and octal number formats, and formats that don't require all four bytes to be explicitly written)."
  - BUGS: "An explicit IPv4-mapped IPv6 address must be supplied in src instead."
  - AF_INET6 cites an older RFC: "See RFC 2373 for further details on the representation of IPv6 addresses." STANDARDS is "POSIX.1-2008." (this page has not followed POSIX.1-2024 to RFC 4291).

**POSIX.1-2024 socket interfaces**
- <https://pubs.opengroup.org/onlinepubs/9799919799/functions/accept.html> — retrieved 2026-10-29 —
  - Synopsis: "int accept4(int socket, struct sockaddr *restrict address, socklen_t *restrict address_len, int flag);"
  - "The accept4() function shall be equivalent to the accept() function, except that the state of O_NONBLOCK" / "on the new file description, and FD_CLOEXEC and FD_CLOFORK on the returned file descriptor" / "shall be determined solely by the flag argument".
  - Flags: SOCK_CLOEXEC "Atomically set the FD_CLOEXEC flag on the new file descriptor."; SOCK_CLOFORK "Atomically set the FD_CLOFORK flag on the new file descriptor."; SOCK_NONBLOCK "Set the O_NONBLOCK file status flag on the new file description."
  - accept(): "If O_NONBLOCK is set on the file description for socket, it is implementation-defined whether O_NONBLOCK will be set on the file description created by accept()"; "FD_CLOEXEC and FD_CLOFORK for the new file descriptor shall be clear, regardless of how they are currently set for socket."
  - EINVAL: "The value of the flag argument is invalid."
  - Rationale: "The SOCK_CLOEXEC and SOCK_CLOFORK flags of accept4() are necessary to avoid a data race in multi-threaded applications."
  - Change history: "Austin Group Defects 411 and 1318 are applied, adding accept4()," and "requiring FD_CLOEXEC and FD_CLOFORK to be clear for the file descriptor returned by accept()".
- <https://pubs.opengroup.org/onlinepubs/9799919799/basedefs/sys_socket.h.html> — retrieved 2026-10-29 —
  - "The header shall define the following socket creation flags, for use in socket(), socketpair(), and accept4()."
  - SOCK_NONBLOCK: "Create a socket file descriptor with the O_NONBLOCK flag atomically set on the new open file description."
  - SOCK_CLOEXEC: "Create a socket file descriptor with the FD_CLOEXEC flag atomically set on that file descriptor."
  - MSG_NOSIGNAL: "No SIGPIPE generated when an attempt to send is made on a stream-oriented socket that is no longer connected."
  - SO_REUSEADDR: "Reuse of local addresses is supported." SO_REUSEPORT was not found on the page.
  - Issue 8 change history: "Austin Group Defects 411 and 1318 are applied, adding SOCK_NONBLOCK, SOCK_CLOEXEC, SOCK_CLOFORK," / "MSG_CMSG_CLOEXEC, MSG_CMSG_CLOFORK, and accept4()." MSG_NOSIGNAL is not in that list.

**Linux behaviour, man-pages 6.19** (every page's colophon names the tarball man-pages-6.19.tar.gz, which man7.org fetched on 2026-09-09)
- <https://man7.org/linux/man-pages/man2/accept.2.html> — retrieved 2026-10-29 —
  - "If flags is 0, then accept4() is the same as accept()."
  - SOCK_NONBLOCK: "Set the O_NONBLOCK file status flag on the open file description (see open(2)) referred to by the new file descriptor."
  - SOCK_CLOEXEC: "Set the close-on-exec (FD_CLOEXEC) flag on the new file descriptor."
  - VERSIONS: "On Linux, the new socket returned by accept() does not inherit file status flags such as O_NONBLOCK and O_ASYNC" "from the listening socket."
  - STANDARDS "POSIX.1-2024."; HISTORY for accept4(): "POSIX.1-2024. Linux 2.6.28, glibc 2.10."
  - EINVAL for accept4(): "invalid value in flags."
- <https://man7.org/linux/man-pages/man2/send.2.html> — retrieved 2026-10-29 —
  - "MSG_NOSIGNAL (since Linux 2.2)"; "Don't generate a SIGPIPE signal if the peer on a stream-oriented socket has closed the connection."; "The EPIPE error is still returned."
  - "This provides similar behavior to using sigaction(2) to ignore SIGPIPE, but, whereas MSG_NOSIGNAL" "is a per-call feature, ignoring SIGPIPE sets a process attribute that affects all threads in the process."
  - EPIPE: "The local end has been shut down on a connection oriented socket." "In this case, the process will also receive a SIGPIPE unless MSG_NOSIGNAL is set."
  - STANDARDS "POSIX.1-2024."; HISTORY "POSIX.1-2008 adds a specification of MSG_NOSIGNAL."
  - The page does not say MSG_NOSIGNAL applies to write(2); it says "The only difference between send() and write(2) is the presence of flags."
- <https://man7.org/linux/man-pages/man7/socket.7.html> — retrieved 2026-10-29 —
  - SO_REUSEADDR: "Indicates that the rules used in validating addresses supplied in a bind(2) call should allow reuse of local addresses." "For AF_INET sockets this means that a socket may bind, except when there is an active listening socket" "bound to the address." "When the listening socket is bound to INADDR_ANY with a specific port then it is not possible to bind to this port for any local address." "Argument is an integer boolean flag."
  - NOTES: "Linux will allow port reuse only with the SO_REUSEADDR option when this option was set both in the previous program" "that performed a bind(2) to the port and in the program that wants to reuse the port."
  - "SO_REUSEPORT (since Linux 3.9)"; "Permits multiple AF_INET or AF_INET6 sockets to be bound to an identical socket address."; "To prevent port hijacking, all of the processes binding to the same address must have the same effective UID."
  - No default is stated for SO_REUSEADDR or SO_REUSEPORT; SO_EXCLUSIVEADDRUSE is not on the page.

**Pins for CURRENCY.md rows** (all checked 2026-10-29)

| Depends on | Pinned | Source |
|---|---|---|
| RFC 4291 | Feb 2006, Draft Standard; no Obsoleted By returned; Updated By 5952, 6052, 7136, 7346, 7371, 8064 | rfc-editor.org/info/rfc4291 |
| RFC 5952 | Aug 2010, Standards Track, Updates 4291; own Obsoleted By and Updated By unread (HTTP 502) | rfc-editor.org/rfc/rfc5952 |
| RFC 3986 | STD 66; §3.2.2 read, §7.4 unread | rfc-editor.org/rfc/rfc3986 |
| POSIX | IEEE Std 1003.1-2024, Open Group Base Specifications Issue 8 | pubs.opengroup.org/onlinepubs/9799919799/ |
| Linux man-pages | 6.19 (man-pages-6.19.tar.gz); pages read: accept(2), send(2), socket(7), inet_pton(3) | man7.org/linux/man-pages/ |

## What would change this

The request's condition: "a cited RFC is obsoleted or updated in a way a rule depends on, the current guidance contradicts a rule (A-19's refusals, SK-037's no-conversion, SK-032's `SO_REUSEADDR` default), or POSIX's current edition specifies a socket interface the library uses differently from the Linux behaviour its specifications state."

**Verdict: it came true in one respect, conditionally on A-19's text, and one part is open. The libraries' seat rules first.** The researcher could not read A-19, SK-032, SK-037 or the library's specifications. Each "contradicts" below is therefore a comparison the seat makes against the quoted text.

1. **A cited RFC obsoleted or updated.**
   - Not met for RFC 4291: the RFC Editor returned no Obsoleted By field, and the highest-numbered updater is 8064. The updater that governs text form, 5952, was read.
   - Open for RFC 5952: its own status was not retrieved (HTTP 502). The only evidence is that no RFC above 8064 updates 4291, and a replacement of 5952 would be expected to say "Updates: 4291" as 5952 does. That is an inference, not a primary.
   - Unverified for RFC 6052, 7136, 7346, 7371 and 8064: not read. Nothing read suggests they touch §2.2 or §2.5.5.
2. **Guidance contradicts a rule.**
   - A-19 would be contradicted by either of these refusals:
     - (a) Refusing an IPv4 octet with leading zeros ("010", "001"). POSIX.1-2024 `inet_pton` says "Leading zeros shall be allowed", within three digits, read as decimal. The refusal agrees with RFC 3986's grammar. The split is POSIX against IETF, so citing POSIX as the source of such a refusal would be wrong.
     - (b) Refusing any IPv6 text form RFC 4291 §2.2 admits: leading zeros inside a field (up to four hex digits), upper-case hex (RFC 4291's own examples are upper case), the uncompressed eight-field form, "::" at either end, or the d.d.d.d tail. RFC 5952 §4 says all implementations MUST accept any legitimate RFC 4291 format.
   - A-19 would not be contradicted by refusing:
     - octal, hex or short IPv4 forms (POSIX "does not accept"; RFC 3986 grammar);
     - a second "::", fields over four hex digits, or empty fields (RFC 4291 §2.2);
     - decimal notation anywhere but the last 32 bits (RFC 5952 §5);
     - zone ids or prefix lengths in an address parser (POSIX lists only the three forms and returns 0 for anything else; RFC 4007 was not read).
   - A reading call for the seat: "::a.b.c.d" (IPv4-compatible). It is deprecated and "New or updated implementations are not required to support this address type" (§2.5.5.1), but it is still a §2.2 text form.
   - SK-037, no-conversion: nothing read contradicts it. The mapped form is defined as an address type. The Linux page says an explicit mapped address must be supplied, and POSIX `inet_pton` returns 0 for a string that is neither valid IPv4 nor valid IPv6. What a dual-stack AF_INET6 listener returns from accept() (ipv6(7), IPV6_V6ONLY) was not read.
   - SK-032, SO_REUSEADDR default: nothing read contradicts it. Facts to check the rule against:
     - On Linux the AF_INET rule is that a socket may bind except while an active listening socket is bound to the address.
     - Linux allows reuse only if both the earlier and the later program set the option.
     - No default is stated.
     - SO_REUSEPORT needs the same effective UID and is not in POSIX.1-2024's `<sys/socket.h>`.
3. **POSIX edition against Linux.** Not met for accept4, SOCK_NONBLOCK, SOCK_CLOEXEC or MSG_NOSIGNAL. The two agree on what they do, and the Linux man pages say STANDARDS "POSIX.1-2024." for accept4 and send. Differences to carry into COMPAT.md:
   - accept4, SOCK_NONBLOCK, SOCK_CLOEXEC and SOCK_CLOFORK are not in POSIX before Issue 8. On Linux, accept4 is from 2.6.28 with glibc 2.10.
   - MSG_NOSIGNAL is POSIX.1-2008 and Linux 2.2.
   - SO_REUSEPORT is Linux 3.9 only.
   - Plain accept(): POSIX says O_NONBLOCK inheritance is implementation-defined; Linux does not inherit it. accept4's flag decides it "solely" in POSIX.
   - POSIX accept() leaves FD_CLOEXEC and FD_CLOFORK clear, so a descriptor from plain accept() is inheritable.
   - SOCK_CLOFORK exists only in POSIX.1-2024. The Linux accept4 flag text read names only SOCK_NONBLOCK and SOCK_CLOEXEC, so Linux support for SOCK_CLOFORK is not established.
   - The Linux inet_pton(3) page cites RFC 2373 where POSIX.1-2024 cites RFC 4291. Do not copy the man page's RFC citation.

## Confidence and gaps

Confidence: high for the quoted POSIX.1-2024 and man-pages 6.19 statements and for RFC 4291 not being obsoleted. Medium for RFC 5952's currency. Medium overall, because several facts have one primary and the comparison against the rules is the seat's to make.

Reading method and budget:
- All pages were read through the fetch tool's extraction, with quotes of 125 characters or fewer. Where it summarised instead of quoting (the §2.5.5.2 diagram, parts of RFC 5952 §5), the digest says so.
- Budget: 12 fetches used. Eleven returned a page. The twelfth, rfc-editor.org/info/rfc5952, returned HTTP 502 and was not retried. One WebSearch, restricted to rfc-editor.org, was also used to locate an IETF text on leading zeros.
- That search found no RFC settling the question. Its results are unopened leads, not cited: [RFC 1117](https://www.rfc-editor.org/rfc/rfc1117.html) and [RFC 3795](https://www.rfc-editor.org/info/rfc3795). The other results were off-topic.

Two independent primaries reached for:
- RFC 4291 not obsoleted, partly: the RFC Editor info page, plus POSIX.1-2024 still citing it.
- No octal, hex or short IPv4 forms: POSIX.1-2024, RFC 3986, and Linux man-pages 6.19.
- accept4 and the SOCK_* flags: POSIX accept page and `<sys/socket.h>`, and Linux accept(2).
- MSG_NOSIGNAL: POSIX `<sys/socket.h>` and Linux send(2).
- The mapped-address layout and text form: RFC 4291 and RFC 5952.

One primary only:
- RFC 5952's currency (none, status unread).
- RFC 5952's MUST-accept sentence (one RFC, stated twice).
- POSIX "Leading zeros shall be allowed" (one page, stated twice; Linux is silent).
- RFC 3986's grammar.
- SO_REUSEADDR semantics (Linux socket(7) only).
- Linux non-inheritance of O_NONBLOCK (Linux accept(2) only).

Unresolved at the budget:
1. RFC 5952's Obsoleted By and Updated By, and any RFC Editor source other than the info page for RFC 4291's status.
2. The texts of RFC 6052, 7136, 7346, 7371 and 8064, and RFC 4291's errata (13 shown, count unconfirmed).
3. A draft replacing RFC 4291 (a 6man "rfc4291bis" is recalled but unverified). The RFC Editor queue and the datatracker were not read.
4. RFC 3986 §7.4, which was beyond the first 100000 characters, and RFC 3986's own Updated By.
5. Austin Group Defects 1573 and 1685 (outside the request's sources), so the reason behind "Leading zeros shall be allowed" is unknown. How libc implementations treat leading zeros is not in any source read.
6. POSIX pages for socket(), socketpair(), send(), setsockopt() and `<netinet/in.h>`, and Linux socket(2) (the SOCK_* version floor rests on accept4's 2.6.28).
7. SO_REUSEADDR for UDP and datagram sockets on Linux, which no page read covers.
8. Linux dual-stack behaviour (ipv6(7), IPV6_V6ONLY, bindv6only) and RFC 3493, RFC 4038 and RFC 6890 on mapped addresses; RFC 4291 points to RFC 4038 for usage.
9. Zone identifiers (RFC 4007 §11, RFC 6874 and its successors) and address prefixes (RFC 4291 §2.3).
10. The kernel's own documentation (docs.kernel.org), not consulted; all Linux behaviour comes from man-pages 6.19.
