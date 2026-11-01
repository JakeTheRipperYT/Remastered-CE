using System;using System.Collections.Generic;
public static class GrassFixture {
 public static void Select(RemasteredCE.Release r){
 var rows=new List<object>();foreach(object x in RemasteredCE.J.Arr(r.Manifest["files"])){string n=RemasteredCE.J.S(RemasteredCE.J.Obj(x),"destination");if(n=="data/shaders.pack"||n=="data/rce_campaign_night_visuals.pack")rows.Add(x);}
 if(rows.Count!=2)throw new Exception("Expected two recipes");r.Manifest["files"]=rows.ToArray();
 }
}
