import re


def remove_dashed_comments(template):
    comments = re.findall("{{!--.*?--}}", template)

    for comment in comments:
        template = template.replace(comment, "", 1)

    return template


def remove_simple_comments(template):
    comments = re.findall("{{!.*?}}", template)

    for comment in comments:
        template = template.replace(comment, "", 1)

    return template


# TODO: Remove this from here if possible
# or integrate better with the result of the logic here.
def parse_variables(template, data):
    tags = re.findall("{{[^#/!].*?}}", template)

    for tag in tags:
        variable = tag[2:-2]
        if variable == "this":
            d = data
        else:
            d = data[variable]
        template = template.replace(tag, str(d), 1)

    return template


# TODO: The comments could probably be done at the highest level before
# anything else is done. Probably way better for performance.
def parse_inner(template, data):
    template = remove_dashed_comments(template)
    template = remove_simple_comments(template)
    return parse_variables(template, data)


class Tag:
    def __init__(self, markup, name, start, end, key=None):
        self.markup = markup
        self.name = name
        self.start = start
        self.end = end
        self.key = key

    def __str__(self):
        s = "Tag: "
        s += repr(self.markup)
        s += " ("
        s += str(self.start)
        s += ", "
        s += str(self.end)
        s += ")"
        return s


class Block:
    def __init__(self, start):
        self.start_tag = start
        self.end_tag = None
        self.else_tag = None

        self.children = []

    def __str__(self):
        s = self.__class__.__name__
        s += " ("
        s += "start_tag=" + str(self.start_tag)
        s += ", end_tag=" + str(self.end_tag)
        s += ", else_tag=" + str(self.else_tag)
        s += ", children=" + str(len(self.children))
        s += ")"
        return s

    def pretty_print(self, level):
        tabs = "\t" * level
        print(tabs + str(self))
        for child in self.children:
            child.pretty_print(level+1)

    def append_child(self, child):
        self.children.append(child)

    def parts(self, template):
        if self.else_tag:
            self.part_inner = template[self.start_tag.end:self.else_tag.start]
            self.part_else = template[self.else_tag.end:self.end_tag.start]
        else:
            self.part_inner = template[self.start_tag.end:self.end_tag.start]

        self.part_outer = template[self.start_tag.start:self.end_tag.end]


class EachBlock(Block):

    def combine(self, template, data):
        result = ""
        items = data[self.start_tag.key]

        if len(items) > 0:
            for item in items:
                part = self.part_inner
                for child in self.children:
                    combined = child.combine(template, item)
                    part = part.replace(child.part_outer, combined, 1)

                result += parse_inner(part, item)
        else:
            if self.else_tag:
                result = self.part_else

        return result


class WithBlock(Block):

    def combine(self, template, data):
        # The most outer Section is faked as html instead of a proper
        # "each" tag. Which means it has no real loop but instead really is a
        # flat strucutre that requires special treatment. In the future
        # this should be changed to a more generic solution probably through
        # the "with" functionality.
        if self.start_tag.markup == "html":
            result = template

            for child in self.children:
                combined = child.combine(template, data)
                result = result.replace(child.part_outer, combined, 1)

            return parse_inner(result, data)
        else:
            result = ""
            item = data[self.start_tag.key]

            if item:
                for child in self.children:
                    combined = child.combine(template, item)
                    result = result.replace(child.part_outer, combined, 1)

                part = self.part_inner
                for child in self.children:
                    combined = child.combine(template, item)
                    part = part.replace(child.part_outer, combined, 1)

                result = parse_inner(part, item)
            else:
                if self.else_tag:
                    result = self.part_else

            return result