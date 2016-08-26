# First I started working with something like this.
# Then I decided, that it wouldn't work.
# So I went to write an NFA-based parser.
# Then I realised it'd be as long as if I just
# wrote it directly. So I wrote it directly.
# Then I thought that it would look nice and run fast
# if it was in LR-like tables.
#
# Here we are again...

# The following program builds the parsing tables.
# The parsing tables consists of two hexadecimal codes.
# One is a state transition and another is an action.

# If action has 0x80 -bit set, it shifts the current state,
# causing goto[state] to be pushed into the table.

# If goto is 0xFF, it pops a transition state from the table.

# To make it easier to create by hand, the table is first
# represented in looser format and only later 'packed' into lists.

# There are some state transitions that are common and cause
# lot of clutter without these assisting functions.
def sskip(table):
    table.update({
        ' ': 0x00FE, '\t': 0x00FE, '\r': 0x00FE, '\n': 0x00FE,
    })
    return table

def pval(table):
    table.update({
        'n': 0x8010, 't': 0x8020, 'f': 0x8030,
        '[': 0x8140,
        '{': 0x8250,
        '"': 0x8060,
        '0': 0x8B76,
        '1': 0x8B70,
        '2': 0x8B70,
        '3': 0x8B70,
        '4': 0x8B70,
        '5': 0x8B70,
        '6': 0x8B70,
        '7': 0x8B70,
        '8': 0x8B70,
        '9': 0x8B70,
        '-': 0x8B78,
    })
    return sskip(table)

def hexv(table, cmd):
    for ch in '0123456789abcdefABCDEF':
        table[ch] = cmd
    return table

# This models the railroad diagram on the json.org -website. Exactly.
# There are actions associated with state stransitions, so sort of..
# this is a recognizer that does parsing actions in middle.
states = {
    0x00: pval({ }),
    # null, true, false
    0x10: { 'u': 0x11 }, 0x11: { 'l': 0x12 }, 0x12: { 'l': 0x13 }, 0x13: { '': 0x05FF },
    0x20: { 'r': 0x21 }, 0x21: { 'u': 0x22 }, 0x22: { 'e': 0x23 }, 0x23: { '': 0x06FF },
    0x30: { 'a': 0x31 }, 0x31: { 'l': 0x32 }, 0x32: { 's': 0x33 }, 0x33: { 'e': 0x34 }, 0x34: { '': 0x07FF },
    # lists
    0x40: pval({ # first
        ']': 0x4F,
    }),
    0x41: sskip({
        ',': 0x0342, ']': 0x034F
    }),
    0x42: pval({ # next
    }),
    0x4F: { '': 0x00FF },
    # dicts
    0x50: sskip({ # first.key
        '"': 0x8060, '}': 0x005F,
    }),
    0x51: sskip({
        ':': 0x52,
    }),
    0x52: pval({ }), # first.val
    0x53: sskip({
        ',': 0x0454, '}': 0x045F,
    }),
    0x54: sskip({ # next.key
        '"': 0x8060
    }),
    0x55: sskip({
        ':': 0x56,
    }),
    0x56: pval({ }), # next.val

    0x5F: { '': 0x00FF },
    # strings
    0x60: { '"': 0x6F, '': 0x0B60, '\\': 0x61 },
    0x61: {
        '"': 0x0B60, '\\': 0x0B60, '/': 0x0B60,
        'b': 0x0D60, 'f': 0x0D60, 'n': 0x0D60, 'r': 0x0D60, 't': 0x0D60,
        'u': 0x8062,
    },
    0x62: hexv({}, 0x0C63),
    0x63: hexv({}, 0x0C64),
    0x64: hexv({}, 0x0C65),
    0x65: hexv({}, 0x0C66),
    0x66: { '': 0x0EFF },
    0x6F: { '': 0x08FF },
    # numbers
    0x70: { # after 1-9
        '0': 0x0BFE, '1': 0x0BFE, '2': 0x0BFE, '3': 0x0BFE, '4': 0x0BFE,
        '5': 0x0BFE, '6': 0x0BFE, '7': 0x0BFE, '8': 0x0BFE, '9': 0x0BFE,
        '.': 0x0B71, 'e': 0x0B73, 'E': 0x0B73,
        '': 0x09FF
    },
    0x71: { # after a dot.
        '0': 0x0B72, '1': 0x0B72, '2': 0x0B72, '3': 0x0B72, '4': 0x0B72,
        '5': 0x0B72, '6': 0x0B72, '7': 0x0B72, '8': 0x0B72, '9': 0x0B72,
    },
    0x72: { # after a dot digit
        '0': 0x0BFE, '1': 0x0BFE, '2': 0x0BFE, '3': 0x0BFE, '4': 0x0BFE,
        '5': 0x0BFE, '6': 0x0BFE, '7': 0x0BFE, '8': 0x0BFE, '9': 0x0BFE,
        'e': 0x0B73, 'E': 0x0B73,
        '': 0x0AFF,
    },
    0x73: { # after eE
        '0': 0x0B75, '1': 0x0B75, '2': 0x0B75, '3': 0x0B75, '4': 0x0B75,
        '5': 0x0B75, '6': 0x0B75, '7': 0x0B75, '8': 0x0B75, '9': 0x0B75,
        '+': 0x0B74, '-': 0x0B74,
    },
    0x74: { # after eE-+
        '0': 0x0B75, '1': 0x0B75, '2': 0x0B75, '3': 0x0B75, '4': 0x0B75,
        '5': 0x0B75, '6': 0x0B75, '7': 0x0B75, '8': 0x0B75, '9': 0x0B75,
    },
    0x75: { # after eE-+ digit
        '0': 0x0BFE, '1': 0x0BFE, '2': 0x0BFE, '3': 0x0BFE, '4': 0x0BFE,
        '5': 0x0BFE, '6': 0x0BFE, '7': 0x0BFE, '8': 0x0BFE, '9': 0x0BFE,
        '': 0x0AFF,
    },
    0x76: { # after 0
        '.': 0x0B71, 'e': 0x0B73, 'E': 0x0B73,
        '': 0x09FF
    },
    0x78: { # '-'
        '0': 0x0B76, '1': 0x0B70, '2': 0x0B70, '3': 0x0B70, '4': 0x0B70,
        '5': 0x0B70, '6': 0x0B70, '7': 0x0B70, '8': 0x0B70, '9': 0x0B70,
    },
}
# This program is different from LR parsing tables quite radically such that it
# is not shifting at every transition. Also there's no GOTO entry for every
# left-hand-side rule, because it is not needed. Every state accepts at most one LHS.
gotos = {
    0x00: 0x00, # accept?
    0x40: 0x41, # list.first
    0x42: 0x41, # list.next
    0x50: 0x51, # dict.first.key
    0x52: 0x53, # dict.first.val
    0x54: 0x55, # dict.next.key
    0x56: 0x53, # dict.next.val
    0x61: 0x60, # string.escape
}

# The non-trivial escape characters are directly dumped.
# So this contains the non-trivial ones only.
escape_characters = {'b': '\b', 'f': '\f', 'n': '\n', 'r': '\r', 't': '\t' }

# Ok. Here we start to pack the state tables.. First of all we create
# character categories by grouping every character by state column.
anychar = frozenset((state, table.get(u'', 0xFFFF))
    for state, table in states.items())
groups = {}
groups[anychar] = ''
for n in range(0, 0x7F):
    catset = frozenset(
        (state, table.get(chr(n), table.get(u'', 0xFFFF)))
        for state, table in states.items())
    if catset in groups:
        groups[catset] += chr(n)
    else:
        groups[catset] = chr(n)

# Then we extract the results into catcode -table. The idea is you clamp
# character ordinal to this range and index from this table. The last
# character '~' happens to be 'anychar', so that simple min(n, 0x7E) works.
catcode = [0 for n in range(0, 0x7F)]
groups.pop(anychar)
columns = [dict(anychar)]
for col, string in sorted(groups.items(), key=lambda a: a[1]):
    for ch in string:
        catcode[ord(ch)] = len(columns)
    columns.append(dict(col))

# The state transitions need to be listed and relabeled by list index.
packedtable = []
mapper = dict((oldlabel, newlabel) for newlabel, oldlabel in enumerate(sorted(states)))

packedgotos = []
for newlabel, oldlabel in enumerate(sorted(states)):
    row = []
    for col in columns:
        code = col[oldlabel]
        action = code >> 8 & 0xFF
        code   = code      & 0xFF
        code = mapper.get(code, code)
        if code == 0xFE:
            code = newlabel
        code = action << 8 | code
        row.append(code)
    packedtable.append(row)
    goto = gotos.get(oldlabel, 255) # drop to blank goto is a bug.
    packedgotos.append(mapper.get(goto, goto))

# And then finally, to allow copy/paste.
print '# generated by build_tables.py program: http://github.com/cheery/json_algorithm'
print 'states = ['
for row in packedtable:
    print '    [',
    for v in row:
        print "0x{:04x},".format(v),
    print '],'
print ']'
print "gotos =",    packedgotos
print "catcode =", catcode

# # These can be used for debugging.
# print "mapping =",  mapper
# # This program does a small consistency check.
# def main():
#     stack = []
#     state = 0x00
#     ds = [] # data stack
#     ss = [] # string stack
#     es = [] # escape stack
#     for ch in read_file("test.json").strip():
#         state = parse_ch(ch, stack, state, ds, ss, es)
#     state = parse_ch(u' ', stack, state, ds, ss, es)
#     if state != 0x00:
#         raise Exception("JSON decode error: truncated")
#     if len(ds) != 1:
#         raise Exception("JSON decode error: too many objects")
#     val = ds.pop()
#     print '#', val
# 
# def read_file(filename):
#     with open(filename, "rb") as fd:
#         return fd.read().decode('utf-8')
# 
# # There's a tutorial in the README.md how to write yourself
# # an engine for driving the tables.
# def parse_ch(ch, stack, state, ds, ss, es):
#     while True:
#         table = states[state]
#         code = table.get(ch, table.get(u'', 0xFFFF))
#         action = code >> 8 & 0xFF
#         code   = code      & 0xFF
#         #print repr(ch), hex(state), hex(action), hex(code)
#         if action == 0xFF and code == 0xFF:
#             raise Exception("JSON decode error: syntax")
#         elif action >= 0x80: # shift
#             stack.append(gotos[state])
#             action -= 0x80
#         if action > 0:
#             do_action(action, ch, ds, ss, es)
#         if code == 0xFF:
#             state = stack.pop()
#         else:
#             if code != 0xFE: # nop
#                 state = code
#             return state
# 
# def do_action(action, ch, ds, ss, es):
#     if action == 0x1:
#         ds.append([])
#     elif action == 0x2:
#         ds.append({})
#     elif action == 0x3:
#         val = ds.pop()
#         ds[len(ds)-1].append(val)
#     elif action == 0x4:
#         val = ds.pop()
#         key = ds.pop()
#         ds[len(ds)-1][key] = val
#     elif action == 0x5:
#         ds.append(None)
#     elif action == 0x6:
#         ds.append(True)
#     elif action == 0x7:
#         ds.append(False)
#     elif action == 0x8:
#         val = u"".join(ss)
#         ds.append(val)
#         ss[:] = []
#         es[:] = []
#     elif action == 0x9:
#         val = int(u"".join(ss))
#         ds.append(val)
#         ss[:] = []
#     elif action == 0xA:
#         val = float(u"".join(ss))
#         ds.append(val)
#         ss[:] = []
#     elif action == 0xB:
#         ss.append(ch)
#     elif action == 0xC:
#         es.append(ch)
#     elif action == 0xD:
#         ss.append(escape_characters[ch])
#     elif action == 0xE:
#         ss.append(unichr(int(u"".join(es), 16)))
#         es[:] = []
#     else:
#         assert False, "JSON decoder bug"
# 
# # if __name__=="__main__":
# #     main()
