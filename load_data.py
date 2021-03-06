from sqlalchemy import create_engine, MetaData, Table
import json
import pandas as pd
from matplotlib.mlab import find
from numpy import *
from matplotlib.mlab import *
from circ_stats import *
from scipy.io import savemat
import sys
import os



# db_url = "sqlite:///"+sys.argv[1]

# table_name = 'swaps'
# data_column_name = 'datastring'
# # boilerplace sqlalchemy setup
# engine = create_engine(db_url)
# metadata = MetaData()
# metadata.bind = engine
# table = Table(table_name, metadata, autoload=True)
# # make a query and loop through
# s = table.select()
# rows = s.execute()
# rs = []
# ds = []


dbs = amap(lambda x: x.split(".db"),os.listdir(sys.argv[1]))
dbs = dbs[amap(len,dbs)>1]

Rows = []
for db in dbs:
	db_url = "sqlite:///"+sys.argv[1]+db[0]+".db"
	table_name = 'swaps'
	data_column_name = 'datastring'
	# boilerplace sqlalchemy setup
	engine = create_engine(db_url)
	metadata = MetaData()
	metadata.bind = engine
	table = Table(table_name, metadata, autoload=True)
	# make a query and loop through
	s = table.select()
	rows = s.execute()
	Rows.append(rows)

def to_pi(angles):
	angles = array(angles)
	idx = angles>pi
	angles[idx] = angles[idx]-2*pi
	return angles

# filter subjects with no real experiment
def get_trials_data(data):
	idx = find([not d['trialdata']['phase'] for d in data["data"]])
	trialdata = [data["data"][i]["trialdata"] for i in idx]
	return trialdata

def filter_data(data):
	trials = []
	for d in data:
		trial = {}
		trial["load"] = d["load"]
		trial["delay"] = d["delay"]
		trial["show"] = d["show"]
		trial["report_color"] = d["report_color"]
		trial["rt"] = d["rt"]

		stims = json.loads(d["trial"])
		stims = json.loads(d["session"])["trial"]
		NT = []
		for i,s in enumerate(stims):
			if s["correct"]:
				trial["T_color"] = s["color"]
				trial["T_pos"] = s["pos_angle"]
			else:
				NT.append([s["color"],s["pos_angle"]])

		for i,[color,pos] in enumerate(NT):
			trial["NT_color"+str(i)] = color
			trial["NT_pos"+str(i)] = pos

		trials.append(trial)
	return trials


all_trials  = {}
for rows in Rows:
	for r in rows:
		if r["datastring"]:
			data=json.loads(r['datastring'])
			workerID = data["workerId"]
			trials_data = get_trials_data(data)
			if len(trials_data) > 50:
				all_trials[workerID] = filter_data(trials_data)



good_workers = all_trials.keys()


X=[]
T_c=[]
T_p = []
NT_c = []
NT_p = []
D=[]
C=[]
loads = []
for wid in good_workers:

	x=[]
	t_c=[]
	t_p=[]
	nt_c=[]
	nt_p=[]	
	d=[]
	c=[]
	for trial in all_trials[wid]:
		load = trial["load"]
		loads.append(load)
		x.append(trial["report_color"])
		t_c.append(trial["T_color"])
		t_p.append(trial["T_pos"])
		d.append(trial["delay"])
		c.append(trial["show"])
		nt_c1=[]
		nt_p1=[]
		for nt in range(load-1):
			nt_c1.append(trial["NT_color"+str(nt)])
			nt_p1.append(trial["NT_pos"+str(nt)])
		nt_c.append(nt_c1)
		nt_p.append(nt_p1)

	X.append(x)
	T_c.append(t_c)
	T_p.append(t_p)
	NT_c.append(nt_c)
	NT_p.append(nt_p)
	D.append(d)
	C.append(c)


x=concatenate(X)
t_c = concatenate(T_c)
t_p = concatenate(T_p)
nt_c = concatenate(NT_c)
nt_p = concatenate(NT_p)
c=concatenate(C)
d=concatenate(D)
c= (c==1)
d=~(d==0)


X_show =[]
T_show =[]
NT_show =[]

X_hide =[]
T_hide =[]
NT_hide =[]

# colapsing all loads
# nt_idx = amap(len,nt_c) >0
# for i,nt in enumerate(nt_c[nt_idx]):
# 	dist_to_nt = abs(circdist(x[nt_idx][i],nt))
# 	close = argsort(dist_to_nt)[0]
# 	X_show.append(x[nt_idx][i])
# 	T_show.append(t_c[nt_idx][i])
# 	NT_show.append(nt[close])

# c = c[nt_idx]
# X_show = array(X_show)
# T_show = array(T_show)
# NT_show = array(NT_show)

# X_hide = X_show[c==0]
# T_hide = T_show[c==0]
# NT_hide =NT_show[c==0]


# X_show = X_show[c==1]
# T_show = T_show[c==1]
# NT_show =NT_show[c==1]


for load in unique(loads):
	if load == 1:
		continue 
	idx = load == loads
	X_show+=[x[idx & c & d]]
	X_hide+=[x[idx & ~c & d]]
	T_show+=[amap(to_pi,t_c[idx & c & d])]
	T_hide+=[amap(to_pi,t_c[idx & ~c & d])]
	NT_show+=[amap(to_pi,nt_c[idx & c & d])]
	NT_hide+=[amap(to_pi,nt_c[idx & ~c & d])]


X_hide=array(X_hide)
T_hide =array(T_hide)
NT_hide =array(NT_hide)
hide_d = {"X": X_hide, "T": T_hide, "NT": NT_hide}

X_show = array(X_show)
T_show = array(T_show)
NT_show = array(NT_show)
show_d = {"X": X_show, "T": T_show, "NT": NT_show}

savemat("show_d.mat",show_d)
savemat("hide_d.mat",hide_d)


