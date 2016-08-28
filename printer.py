import sys, random, time
import verifier

# You may either feed this printer a json file, or let it
# create a random json object to print.
def main():
    if len(sys.argv) < 2:
        obj = synth_json()
    else:
        with open(sys.argv[1], "r") as fd:
            obj = verifier.parse_string(fd.read().decode('utf-8'), set())
    scan = Scanner()
    stringify(scan, obj)
    scan.finish()

# A slightly bad random json object generator.
# It's not a proper test for most things. But it's
# enough to show how the pretty printer works.
def synth_json(depth=0):
    if depth > 4:
        return synth_string(depth)
    return random.choice(synths)(depth)

def synth_dict(depth):
    out = {}
    for i in range(random.randint(0, 10)):
        out[synth_string(depth)] = synth_json(depth + 1)
    return out

def synth_list(depth):
    out = []
    for i in range(random.randint(0, 10)):
        out.append(synth_json(depth + 1))
    return out

def synth_const(depth):
    r = random.random() 
    if r < 0.1:
        return random.choice([True, False, None])
    elif r < 0.5:
        return random.randint(0, 1000)
    elif r < 0.8:
        return synth_string(depth)
    else:
        return 1000 * (
            random.random() * random.random()
            - random.random() * random.random())

def synth_string(depth):
    return random.choice(funny_strings)

funny_strings = [
        u"progging along", u"chug", u"gunk", u"hazard", u"code", u"bljarmer", u"xok",
        u"log", u"blog", u"farmer", u"punk", u"zebra", u"radio", u"epsilon", u"gamma",
        u'world "Hello" world',
        u''.join(map(chr, range(40))),
        u"\\",
        u''.join(map(unichr, range(0x2020, 0x203f))),
        u''.join(map(unichr, range(0x4020, 0x4040))),
]

synths = [synth_dict, synth_list, synth_const]

# The algorithm used here is a generic pretty printer.
# This specifies the layout and printout that is desired.
def stringify(scan, obj):
    if isinstance(obj, dict):
        scan.left()(u"{").blank(u"", 4)
        more = False
        for key, value in sorted(obj.items(), key=lambda a: a[0]):
            if more:
                scan(u",").blank(u" ", 4)
            scan.left()
            scan(escape_string(key)+u': ')
            stringify(scan, value)
            scan.right()
            more = True
        scan.blank(u"", 0)(u"}").right()
    elif isinstance(obj, list):
        scan.left()(u"[").blank(u"", 4)
        more = False
        for item in obj:
            if more:
                scan(u",").blank(u" ", 4)
            stringify(scan, item)
            more = True
        scan.blank(u"", 0)(u"]").right()
    elif isinstance(obj, (str, unicode)):
        scan(escape_string(obj))
    elif obj is None:
        scan(u"null")
    elif obj == True:
        scan(u"true")
    elif obj == False:
        scan(u"false")
    elif isinstance(obj, (int, long, float)): # Would also recognize booleans if
        scan(str(obj)) # hack.                # you let it do so.
                       # Only works if this
                       # prints the floats in C notation.
                       # Otherwise you need to come up
                       # with your own float formatter.
    else:
        assert False, "no handler: " + repr(obj)

# This is the easiest point of failure in your stringifier program.
def escape_string(string):
    out = [u'"']
    for ch in string:
        n = ord(ch)
        if 0x20 <= n and n <= 0x7E or 0xFF < n: # remove the last part in cond if you don't want
            if ch == u'\\':                     # unicode printed out for some reason.
                ch = u'\\\\'
            elif ch == u'"':
                ch = u'\\"'
        else:
            a = u"0123456789abcdef"[n >> 12]
            b = u"0123456789abcdef"[n >> 8  & 15]
            c = u"0123456789abcdef"[n >> 4  & 15]
            d = u"0123456789abcdef"[n       & 15]
            ch = u'u' + a + b + c + d
            ch = u'\\' + character_escapes.get(n, ch)
        out.append(ch)
    out.append(u'"')
    return u"".join(out)

character_escapes = {8: u'b', 9: u't', 10: u'n', 12: u'f', 13: u'r'}

# The scanner runs three line widths before the printer and checks how many
# spaces the blanks and groups take. This allows the printer determine
# whether the line or grouping should be broken into multiple lines.
class Scanner(object):
    def __init__(self):
        self.printer = Printer()
        self.stream = []
        self.stack = []
        self.lastblank = None
        self.left_total = 1
        self.right_total = 1 # makes sure we won't treat the first
                             # item differently than others.

    def left(self):
        return self(Left())

    def right(self):
        return self(Right())

    def blank(self, text, indent=0):
        return self(Blank(text, indent))

    def __call__(self, x):
        if isinstance(x, Left):
            x.size = -self.right_total
            self.stack.append(x)
        elif isinstance(x, Right):
            if len(self.stack) > 0:
                self.stack.pop().size += self.right_total
        elif isinstance(x, Blank):
            if self.lastblank is not None:
                self.lastblank.size += self.right_total
            self.lastblank = x
            x.size = -self.right_total
            self.right_total += len(x.text)
        else:
            self.right_total += len(x)
        self.stream.append(x)
        while len(self.stream) > 0 and self.right_total - self.left_total > 3*self.printer.margin:
            self.left_total += self.printer(self.stream.pop(0))
        return self

    def finish(self):
        if self.lastblank is not None:              # Without this the last blank
            self.lastblank.size += self.right_total # gets very different treatment.
        while len(self.stream) > 0:
            self.printer(self.stream.pop(0))
        sys.stdout.write('\n')

# Printer keeps the track of layout during printing.
class Printer(object):
    def __init__(self):
        self.margin = 80
        self.layout = Layout(None, 80, False)
        self.spaceleft = 80
        self.spaces = 80

    def __call__(self, x):
        if isinstance(x, Left):
            self.layout = Layout(self.layout,
                self.spaces,
                x.size < 0 or self.spaceleft < x.size)
            return 0
        elif isinstance(x, Right):
            if self.layout.parent:
                self.layout = self.layout.parent
            return 0
        elif isinstance(x, Blank):
            if x.size < 0 or self.spaceleft < x.size or self.layout.force_break:
                self.spaces = self.layout.spaces - x.indent
                self.spaceleft = self.spaces
                sys.stdout.write('\n' + ' '*(self.margin - self.spaces))
            else:
                sys.stdout.write(x.text.encode('utf-8'))
                self.spaceleft -= len(x.text)
            return len(x.text)
        else:
            sys.stdout.write(x.encode('utf-8'))
            self.spaceleft -= len(x)
            return len(x)

# These small objects are scanner and printer internals.
class Layout(object):
    def __init__(self, parent, spaces, force_break):
        self.parent = parent
        self.spaces = spaces
        self.force_break = force_break

# These objects are mutated by the scanner, so they cannot be
# reused. Users of the pretty printer should not create them themselves.
class Left(object):
    def __init__(self):
        self.size = 0

class Right(object):
    pass

class Blank(object):
    def __init__(self, text, indent=0):
        self.text = text
        self.indent = indent
        self.size = 0

if __name__ == '__main__':
    main()
