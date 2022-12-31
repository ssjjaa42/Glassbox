from os import path


class Script:
    lines = []
    index = 0

    def __init__(self, filepath):
        with open(filepath, 'r') as f:
            self.lines = f.readlines()

    @staticmethod
    def sanitize(text):
        punctuation = "!?:,.\n\t\'\"-"
        text = text.lower()
        for p in punctuation:
            text = text.replace(p, '')
        return text

    def eval(self, text):
        text = self.sanitize(text)
        line = self.sanitize(self.lines[self.index])
        error_count = 0
        text_broke = text.split(' ')
        line_broke = line.split(' ')
        if len(line_broke) < len(text_broke):
            self.nextline()
            line_broke.extend(self.sanitize(self.lines[self.index]).split(' '))
        if len(line_broke) > len(text_broke):
            return False
        for i in range(len(line_broke)):
            if text_broke[i] != line_broke[i]:
                error_count += 1
        return error_count < 3

    def nextline(self):
        text = self.lines[self.index]
        self.index += 1
        return text[:-1]

    def has_next(self):
        return self.index < len(self.lines)

    def reset(self):
        self.index = 0


# Debug. Just testing the functions.
if __name__ == '__main__':
    sc = Script(path.join(path.curdir, 'data', 'scripts', 'trouble.txt'))
    match = True
    while match and sc.has_next():
        print(sc.nextline())
        tex = input()
        if sc.eval(tex):
            sc.nextline()
            match = True
        else:
            match = False
            