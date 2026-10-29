import json, sys, tempfile, unittest
from pathlib import Path
import seed
class SeedTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory(); self.addCleanup(self.t.cleanup); self.p=Path(self.t.name); self.oracle=self.p/'oracle.py'; self.oracle.write_text("import csv,json,sys\np=sys.argv[1]\nr=json.load(open(p)) if p.endswith('.json') else list(csv.DictReader(open(p)))\nsys.exit(7 if any(x.get('bug')=='yes' for x in r) else 0)\n"); self.policy=self.p/'policy.json'; self.policy.write_text(json.dumps({'fields':{'bug':'keep','id':'replace','owner':'replace'},'relationships':[['id','owner']]})); self.cmd=[sys.executable,str(self.oracle),'{input}']
 def test_json(self):
  source=self.p/'x.json'; source.write_text(json.dumps([{'bug':'no','id':'CANARY1','secret':'PRIVATE'}, {'bug':'yes','id':'CANARY2','owner':'CANARY2','secret':'PRIVATE'}])); r=seed.run(source,self.policy,self.p/'out',self.cmd); text=(self.p/'out/fixture.json').read_text(); rows=json.loads(text); self.assertEqual(len(rows),1); self.assertEqual(rows[0]['id'],rows[0]['owner']); self.assertNotIn('CANARY',text); self.assertNotIn('PRIVATE',text); self.assertFalse(r['privacy_guarantee'])
 def test_csv(self):
  source=self.p/'x.csv'; source.write_text('bug,id,secret\nno,CANARY1,PRIVATE\nyes,CANARY2,PRIVATE\n'); r=seed.run(source,self.policy,self.p/'out',self.cmd); self.assertEqual(r['output_records'],1); self.assertNotIn('PRIVATE',(self.p/'out/fixture.csv').read_text())
 def test_changed_failure_rejected(self):
  source=self.p/'x.json'; source.write_text('[{"bug":"yes"}]'); self.policy.write_text('{"fields":{"bug":"replace"}}');
  with self.assertRaisesRegex(ValueError,'transformation'): seed.run(source,self.policy,self.p/'out',self.cmd)
  self.assertFalse((self.p/'out').exists())
 def test_no_failure(self):
  source=self.p/'x.json'; source.write_text('[{"bug":"no"}]');
  with self.assertRaises(ValueError): seed.run(source,self.policy,self.p/'out',self.cmd)
 def test_invalid_relationship(self):
  with self.assertRaises(ValueError): seed.prepare([],{'fields':{'a':'keep','b':'replace'},'relationships':[['a','b']]})
 def test_existing_output(self):
  source=self.p/'x.json'; source.write_text('[{"bug":"yes"}]'); (self.p/'out').mkdir()
  with self.assertRaises(ValueError): seed.run(source,self.policy,self.p/'out',self.cmd)
 def test_second_bug(self):
  source=self.p/'x.json'; source.write_text('[{"bug":"yes","id":"CANARY"},{"bug":"yes","id":"OTHER"}]'); self.oracle.write_text("import json,sys\nr=json.load(open(sys.argv[1])); sys.exit(9 if len(r)>=2 and all(x.get('bug')=='yes' for x in r) else 0)\n"); r=seed.run(source,self.policy,self.p/'out',self.cmd); self.assertEqual(r['failure_exit_code'],9); self.assertEqual(r['output_records'],2)
if __name__=='__main__': unittest.main()
