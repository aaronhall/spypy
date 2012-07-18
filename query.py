import sunburnt

solr = sunburnt.SolrInterface("http://localhost:8181/solr/spypy/")

results = solr.query(title='strings', text="strings").execute()

print type(results)
print dir(results)
print repr(results)
print results.more_like_this
print results.more_like_these
print results.highlighting
print results.status
print results.interesting_terms


print

num = 1
for res in results:
    print "%s: %s" % (num, res['title'])
    num += 1
