# JSON Decoding Algorithm

Everyone and their dog already has a json parsing and
encoding library. So this module is more of a fun curiosity
rather than an useful tool. 

Now even your pet rock is able to parse JSON.

## Parsing tables for JSON

The code in the [build_tables.py](build_tables.py)
constructs a parsing table that matches on the railroad
diagrams at http://json.org/

There's a recognizer that can push&pop states into a stack.
Every state transition is associated with action code that
is separate from the recognizer and allows you to parse the
contents of the input correctly.

## Tutorial for implementing a JSON decoder or parser

Write the following program in your programming language
of choice:

    def parse(input):
        stack = []
        state = 0x00
        ds = [] # data stack
        ss = [] # string stack
        es = [] # escape stack
        for ch in input:
            cat = catcode[min(ord(ch), 0x7E)]
            state = parse_ch(cat, ch, stack, state, ds, ss, es, chart)
        state = parse_ch(catcode[32], u'', stack, state, ds, ss, es, chart)
        if state != 0x00:
            raise Exception("JSON decode error: truncated")
        if len(ds) != 1:
            raise Exception("JSON decode error: too many objects")
        return ds.pop()

    def parse_ch(cat, ch, stack, state, ds, ss, es, chart):
        while True:
            code = states[state][cat]
            action = code >> 8 & 0xFF
            code   = code      & 0xFF
            if action == 0xFF and code == 0xFF:
                raise Exception("JSON decode error: syntax")
            elif action >= 0x80: # shift
                stack.append(gotos[state])
                action -= 0x80
            if action > 0:
                do_action(action, ch, ds, ss, es)
            if code == 0xFF:
                state = stack.pop()
            else:
                state = code
                return state
        return state

    # This action table is unique for every language.
    # It also depends on which structures you want to
    # generate.
    def do_action(action, ch, ds, ss, es):
        if action == 0x1:              # push list
            ds.append([])
        # Push object to ds
        elif action == 0x2:            # push object
            ds.append({})
        elif action == 0x3:            # pop & append
            val = ds.pop()
            ds[len(ds)-1].append(val)
        elif action == 0x4:            # pop pop & setitem
            val = ds.pop()
            key = ds.pop()
            ds[len(ds)-1][key] = val
        elif action == 0x10:           # push null
            ds.append(None)
        elif action == 0x20:           # push true
            ds.append(True)
        elif action == 0x30:           # push false
            ds.append(False)
        elif action == 0x40:           # push string
            val = u"".join(ss)
            ds.append(val)
            ss[:] = [] # clear ss and es stacks.
            es[:] = []
        elif action == 0x50:
            val = int(u"".join(ss))    # push int
            ds.append(val)
            ss[:] = [] # clear ss stack.
        elif action == 0x60:
            val = float(u"".join(ss))  # push float
            ds.append(val)
            ss[:] = []
        elif action == 0xA:            # push ch to ss
            ss.append(ch)
        elif action == 0xB:            # push ch to es
            es.append(ch)
        elif action == 0xC:            # push escape
            ss.append(unichr(escape_characters[ch]))
        elif action == 0xD:            # push unicode point
            ss.append(unichr(int(u"".join(es), 16)))
            es[:] = []
        else: # This is very unlikely to happen. But make
              # a crashpoint here if possible.
              # Also if you write it in parts, let this line
              # be the first one you write into this routine.
            assert False, "JSON decoder bug"

    # Non-trivial escape characters. At worst you can
    # 'switch' or 'if/else' them into do_action -function.
    escape_characters = {'b': 8, 't': 9, 'n': 10, 'f': 12, 'r': 13}

Add the lists 'states', 'gotos', 'catcode' from
[json.txt](json.txt)
in this directory/repository. Add them into same file under
your application. Also add the comment in that file so that
your code stays maintainable.

If the file is not in the correct format, write a reformatter. DO
NOT try to reformat it by hand to avoid errors.

## Recreational use

This can be probably used to generate random JSON strings as
well. I haven't tried to do that. :D Could be fun and
pointless.

## Bugfixes

There is some verification that the state table is correct.
I have made a program that goes through every state
transition.

If you find a bug in the tables, do not modify them. Modify
the program `build_tables.py` or file an issue in github.com.

## License

[MIT](LICENSE.md) License

Copyright (c) 2016 Henri Tuhola

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
