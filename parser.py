#!/usr/bin/env python

"""
Schema

    title
    parent_titles
    type = [ section | function | pre | blockquote ]
    version_added           # p.versionadded

Type heirarchy

Book (a collection of pages, like Library, Language, Tutorial, pip lib documentation)
    Page
        Section
            FunctionDL
                Function
            ClassDL
                Class
            Table
            Highlighted


"""

import sys
import os
import glob
from pyquery import PyQuery



class Function(object):

    def __init__(self, dl):
        self.dl = dl

        print "-----"
        print self.class_name
        print self.name
        print self.full_name
        print self.signature
        print self.permalink
        print self.definition

    @property
    def class_name(self):
        return self.dl('dt tt.descclassname').text().rstrip('.')

    @property
    def name(self):
        return self.dl('dt tt.descname').text().replace("\n", ' ')

    @property
    def signature(self):
        return self.dl('dt').children().not_('tt, a.headerlink').text()

    @property
    def full_name(self):
        return "%s.%s" % (self.class_name, self.name)

    @property
    def definition(self):
        return self.dl('dd p').text().replace("\n", ' ')

    @property
    def permalink(self):
        return self.dl('dt a.headerlink').attr('href')


class Section(object):
    def __init__(self, section):
        self.section = section.children().not_('.section')

    def __repr__(self):
        return "%s\n%s" % (">>> %s <<<" % self.header, self.paragraphs)

    @property
    def header(self):
        return self.section('h1, h2, h3, h4, h5, h6').text().encode('utf8')
    
    @property
    def first_paragraph(self):
        raise NotImplementedError()

    @property
    def paragraphs(self):
        p = self.section.filter('p')
        if p:
            return p.text().replace("\n", ' ').encode('utf8')
        else:
            return "<None>"

    @property
    def funcs(self):
        func_dls = self.section.filter('dl.function')

        funcs = []

        if func_dls:
            for el in func_dls:
                funcs.append(Function(PyQuery(el)))

        return funcs



class Page(object):
    def __init__(self, filepath):
        f = file(filepath)

        self.d = PyQuery(f.read())

    def __repr__(self):
        lines = []
        print self.title
        #lines.append(">>>>>>> %s <<<<<<<" % self.title)

        for section in self.sections:
            print repr(section)
            #lines.append(repr(section))

        return "\n".join(lines)


    @property
    def title(self):
        return self.d('h1').text()

    @property
    def sections(self):
        root = self.d('.body')
        return self._get_sections(root)

    def _get_sections(self, parent, level=1):
        leaves = parent.children('.section')

        sections = []

        for l in leaves:
            leaf = PyQuery(l)

            #print "%s> %s (%s)" % ("--"*level, type(leaf), len(leaf))
            s = Section(leaf)
            sections.append(s)

            sections += self._get_sections(leaf, level+1)

        return sections

class Collection(object):
    def iterpages(self):
        for f in self.files:
            yield Page(f)

class PythonLibraryCollection(Collection):
    @property
    def files(self):
        path = "/home/ubuntu/spypy/docs/library"
        return glob.glob(os.path.join(path, '*.htm*'))
        
class PythonTutorialCollection(Collection):
    @property
    def files(self):
        path = "/home/ubuntu/spypy/docs/tutorial"
        return glob.glob(os.path.join(path, '*.htm*'))



if __name__ == "__main__":
    import sunburnt

    solr_interface = sunburnt.SolrInterface("http://localhost:8983/solr/")


    coll = PythonTutorialCollection()

    for page in coll.iterpages():
        print page
        print
