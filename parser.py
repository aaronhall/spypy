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
import hashlib


class Function(object):

    def __init__(self, dl):
        self.dl = dl

        """DEBUG!
        print "-----"
        print self.parents
        print self.name
        print self.fqn
        print self.signature
        print self.permalink
        print self.definition
        """


    @property
    def id(self):
        h = hashlib.new('sha1')
        h.update(("%s%s" % (self.fqn, self.definition)).encode('utf8'))

        return h.hexdigest()

    @property
    def parents(self):
        return self.dl('dt tt.descclassname').text().rstrip('.').split('.')

    @property
    def name(self):
        return self.dl('dt tt.descname').text().replace("\n", ' ')

    @property
    def signature(self):
        return self.dl('dt').children().not_('tt, a.headerlink').text()

    @property
    def fqn(self):
        """Fully-qualified name"""
        #return "%s.%s" % ('.'.join(self.parents), self.name)
        return '.'.join(self.parents + [self.name])

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
        return self.header
        #return "%s\n%s" % (">>> %s <<<" % self.header, self.text)

    @property
    def id(self):
        h = hashlib.new('sha1')
        h.update(("%s%s" % (self.header, self.text)).encode('utf8'))

        return h.hexdigest()

    @property
    def header(self):
        return self.section('h1, h2, h3, h4, h5, h6').text()

    @property
    def permalink(self):
        return self.section('h1, h2, h3, h4, h5, h6').children('a').attr('href')
    
    @property
    def first_paragraph(self):
        raise NotImplementedError()

    @property
    def text(self):
        p = self.section.filter('p')
        if p:
            return p.text().replace("\n", ' ')
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

class Corpus(object):
    def iterpages(self):
        for f in self.files:
            yield Page(f)

class Python2LibraryCorpus(Corpus):
    @property
    def files(self):
        path = "/home/ubuntu/spypy/docs/library"
        return glob.glob(os.path.join(path, '*.htm*'))
        
class Python2TutorialCorpus(Corpus):
    @property
    def files(self):
        path = "/home/ubuntu/spypy/docs/tutorial"
        return glob.glob(os.path.join(path, '*.htm*'))

class Python2HowtoCorpus(Corpus):
    @property
    def files(self):
        path = "/home/ubuntu/spypy/docs/howto"
        return glob.glob(os.path.join(path, '*.htm*'))



if __name__ == "__main__":
    import sunburnt
    import time

    t_start = time.time()

    solr = sunburnt.SolrInterface("http://localhost:8181/solr/spypy/")

    print "DELETING ALL DOCUMENTS FROM THE INDEX IN 5 SECONDS!"
    time.sleep(5)
    solr.delete_all()


    corpuses = [
        Python2LibraryCorpus(),
        Python2TutorialCorpus(),
        Python2HowtoCorpus(),
    ]

    doc_count = 0

    for corpus in corpuses:
        for page in corpus.iterpages():
            for section in page.sections:
                doc = {
                    'id': section.id,
                    'title': section.header,
                    #'parent': section.parent,
                    'text': section.text,
                    'permalink': section.permalink,
                }

                print "<Section %s>" % doc['id']
                solr.add(doc)
                doc_count += 1

                for func in section.funcs:
                    try:
                        fdoc = {
                            'id': func.id,
                            'f_name': func.name,
                            #'f_parents': func.parents,
                            'f_fqn': func.fqn,
                            'f_definition': func.definition,
                            'f_signature': func.signature,
                        }
                        print "  <Function %s>" % fdoc['id']

                        solr.add(fdoc)
                        doc_count += 1
                    except Exception, e:
                        raise e
                        print "  [!!!] <EXCEPTION @ %s: %s>" % (fdoc['id'], e)
                        #time.sleep(1)
    
    print "Committing...",
    t_com_start = time.time()
    solr.commit()
    print "Done (%s)" % (time.time() - t_com_start)

    print "Optimizing index...",
    t_opt_start = time.time()
    solr.optimize()
    print "Done (%s)" % (time.time() - t_opt_start)


    print
    print "Indexed %s docs in %ss" % (doc_count, time.time() - t_start)
    print
