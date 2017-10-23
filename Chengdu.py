# -*- coding: utf-8 -*-
from math import *
import matplotlib.pyplot as plt
import numpy as np
import os
import os.path
import time
#from list import *
from test import *
import sys

#平面上求两点相对方向
#完全当作平面几何进行求解
#只适合两点距离很近的时候（小于1KM）
def calAngle(aLa,aLo,bLa,bLo):
	angle = 0
	if bLa == aLa and bLo == aLo:
		angle = -100
		return angle
	#维度相等
	elif bLa == aLa:
		if bLo > aLo:
			angle = 90
		else:
			angle = 270
		return angle
	elif bLo == aLo:
		if bLa > aLa:
			angle = 0
		else:
			angle = 180
	else:
		angle = atan((bLo-aLo)*cos(bLa*pi/180)/(bLa-aLa))
		angle = angle * 180/pi
		if aLa<bLa and aLo<bLo:
			return angle
		elif aLa<bLa and aLo>bLo:
			angle = angle + 360
		else:
			angle = 180 + angle
	return angle

#极坐标法
#思路就是将地球放在一个球坐标系中并适当调整三个参数的起始点以减少后面的运算量，
#然后将各点由球坐标转化为直角坐标，
#之后依据平面法向量的定理求得二面夹角也就是航向，
#之后转化为符合航向定义的度数。
def calAngle2(lat1,lon1,lat2,lon2):
	dlat = lat2 - lat1
	dlon = lon2 - lon1
	y = sin(dlon*pi/180)*cos(lat2*pi/180)
	x = cos(lat1*pi/180)*sin(lat2*pi/180)-sin(lat1*pi/180)*cos(lat2*pi/180)*cos(dlon*pi/180)
	if y > 0:
		if x > 0:
			tc1 = atan(y/x)
		if x < 0:
			tc1 = pi - atan(-y/x)
	   	if x == 0:
	   		tc1 = pi/2
	if y < 0:
		if x > 0:
			tc1 = -atan(-y/x)
	   	if x < 0:
	   		tc1 = atan(y/x)-pi
	   	if x == 0:
	   		tc1 = -1*pi/2
	if y == 0:
		if x > 0:
			tc1 = 0
	   	if x < 0:
	   		tc1 = pi
	   	if x == 0:
	   		tc1 = -1
	return tc1/pi*180

#创建文件夹
def mkdir(path):
	# 去除首位空格
	path = path.strip()
	# 去除尾部 \ 符号
	path = path.rstrip("\\")
	# 判断路径是否存在
	# 存在     True
	# 不存在   False
	isExists = os.path.exists(path)
	# 判断结果
	if not isExists:
		# 如果不存在则创建目录
		# 创建目录操作函数
		os.makedirs(path)
		print path + ' 创建成功'
		return True
	else:
		# 如果目录存在则不创建，并提示目录已存在
		print path + ' 目录已存在'
		return False

#输入两点经纬度，输出距离（单位：米）
def distance(position1,position2):
	a = position1[1] - position2[1]
	b = position1[0] - position2[0]
	distance = 2*asin(sqrt(sin(a/2)*sin(a/2)+cos(position1[1])*cos(position2[1])*sin(b/2)*sin(b/2)))*6378.13
	return distance

#样本数据集包含10000+辆成都出租车的行驶轨迹记录，每两次采样的时间间隔约为10~15sec
def findDirection():
	# 依次读各个文件
	#写出文件夹
	s = os.sep  # 根据unix或win，s为\或/
	root = r'E:' + s + 'VNDN' + s + 'Chengdu'
	out1 = root + s + 'direction result 60sec'
	mkdir(out1)
	data_sourse = root + s + '60sec_taxi_log_2008_by_id'
	list = os.listdir(data_sourse)  # 列出目录下的所有文件
	for line in list:
		filename2 = data_sourse + s + line
		print filename2
		try:
			f_r = open(filename2, 'r')
		except IOError:
			continue

		# 行驶方向结果写出
		w_filename2 = out1 + s + line.split('.')[0] + '.csv'
		try:
			f_w = open(w_filename2, 'w')
		except IOError:
			continue
		line_before = f_r.readline()  # 第一行不能主动跟别人比对
		line_now = f_r.readline()#line_now可以跟line_before比对
		count = 1
		state = 'move'
		if line_before:#排除空文件第一行为空的危险
			state_start_time = int(line_before.split(',')[3].split('.')[0])
		state_end_time = 0.0
		#用来判断停车时间是否构成5min
		judge_stop = False
		judge_stop_start_time = 0.0
		#用来判断运动时间是否达到5min
		judge_move = False
		judge_move_start_time = 0.0
		judge_move_start_position = [0.0, 0.0]
		move_pending_array = []
		stop_pending_array = []
		while line_now:
			#首先读取当前时刻和上一时刻的数据
			try:
				lon_now,lat_now,time_now = float(line_now.split(',')[2]),float(line_now.split(',')[1]),int(line_now.split(',')[3].split('.')[0])
			except ValueError:
				continue
			try:
				lon_before,lat_before,time_before = float(line_before.split(',')[2]),float(line_before.split(',')[1]),int(line_before.split(',')[3].split('.')[0])
			except ValueError:
				continue
			dis = distance([lon_now,lat_now],[lon_before,lat_before])

			# 特别处理时间间隔大于3600的情况
			if abs(time_now - time_before) > 3600:
				if state == 'stop':
					if judge_move:  # 这时需要把这些记录当作停止记录写出去
						judge_move = False  # 初始化运动状态切换到静止态的判断条件
						# 写出列表里的待写出项（历史项）
						for str_item in move_pending_array:
							rec = str_item.split(',')
							w_str = '-1,stop,' + rec[2] + ',' + rec[3] + ',' + rec[4] + ',' + rec[5]
							f_w.write(w_str)
						move_pending_array = []  # 写出后，清空数组
					# 输出现在的这条stop记录
					w_str = '-1,stop,' + str(time_now) + ',' + str(lon_now) + ',' + str(lat_now) + ',' + str(dis) + '\n'
					f_w.write(w_str)
					judge_move = False
				else:
					if judge_stop:  # 需要把待定stop的记录变成真的stop
						for str_item in stop_pending_array:
							rec = str_item.split(',')
							w_str = str(-1) + ',stop,' + rec[2] + ',' + rec[3] + ',' + rec[4] + ',' + rec[5]
							f_w.write(w_str)
						stop_pending_array = []  # 写出后，清空数组
						state = 'stop'  # 将状态切换到stop状态
						judge_move = False
					else:  # 否则将当前这条（3600后的第一条）作为stop处理
						# 输出现在的这条stop记录
						w_str = str(-1) + ',stop,' + str(time_now) + ',' + str(lon_now) + ',' + str(
							lat_now) + ',' + str(dis) + '\n'
						f_w.write(w_str)
						state = 'stop'  # 将状态切换到stop状态
						judge_move = False
				line_before = line_now
				line_now = f_r.readline()  # 读新行
				continue

			if state == 'stop':#如果当前是停止状态
				if distance([lon_now,lat_now],[lon_before,lat_before]) < 10:#当前这条相对于上条记录是停止
					if judge_move:#倘若之前是在一个move待定周期
						# 这个待定周期作废了，待定周期里面的运动记录不输出
						# 清空待写出列表
						judge_move = False
						move_pending_array = []
					#输出现在的这条stop记录
					w_str = str(-1) + ',stop,' + str(time_now) + ',' + str(lon_now) + ',' + str(lat_now) +','+str(dis)+ '\n'
					f_w.write(w_str)
				else:#这条记录相比于上一条是运动了的，检查是不是在运动待定周期
					if judge_move:#在一个move检查周期内（检查move有没有达到1min）
						if (time_now - judge_move_start_time) > 60 :
							state = 'move'#切换到运动状态
							judge_stop = False#初始化运动状态切换到静止态的判断条件
							#写出列表里的待写出项（历史项）
							for str_item in move_pending_array:
								f_w.write(str_item)
								count += 1
							move_pending_array = []#写出后，清空数组
							#当前的这条记录也要写出去
							angle = calAngle(lat_before, lon_before,lat_now, lon_now)
							w_str = str(count) + ',' + str(angle) + ',' + str(time_now) + ',' + str(lon_now) + ',' + str(lat_now) +','+str(dis)+ '\n'
							f_w.write(w_str)
							count += 1
						else:
							#虽然在运动，但还没满足状态条件，先写到列表里
							angle = calAngle(lat_before, lon_before,lat_now, lon_now)
							w_str = str(count + len(move_pending_array)) + ',' + str(angle) + ',' + str(time_now) + ',' + str(lon_now) + ',' + str(lat_now) +','+str(dis)+ '\n'
							move_pending_array.append(w_str)
					else:#开启一个move待定周期，记录待定周期的开始时间
						judge_move = True
						judge_move_start_time = time_now
						#先写到列表里
						angle = calAngle(lat_before, lon_before,lat_now, lon_now)
						w_str = str(count + len(move_pending_array)) + ',' + str(angle) + ',' + str(time_now) + ',' + str(lon_now) + ',' + str(lat_now) + ','+str(dis) + '\n'
						move_pending_array.append(w_str)
			else:#当前是运动周期
				if distance([lon_now,lat_now],[lon_before,lat_before]) >= 10:#且当前这条记录相较于上条也运动，保持运动状态，写出
					if judge_stop:
						# 这个stop待定周期作废了
						judge_stop = False
						#把这个待定周期里面的记录写出去
						for str_item in stop_pending_array:
							rec = str_item.split(',')
							w_str = rec[0] + ',' + rec[1] + ',' + rec[2] + ',' + rec[3] + ',' + rec[4] + ',' + rec[5].split('\n')[0]+',pending stop\n'
							f_w.write(w_str)
							count += 1
						stop_pending_array = []
					#写出当前这条运动记录
					angle = calAngle(lat_before, lon_before,lat_now, lon_now)
					w_str = str(count) + ',' + str(angle) + ',' + str(time_now) + ',' + str(lon_now) + ',' + str(lat_now) +','+str(dis)+ '\n'
					f_w.write(w_str)
					count += 1
				else:#这条记录相比于上一条是静止的，检查是否在静止待定周期
					if judge_stop:#在一个stop检查周期内（检查stop有没有达到10min）
						if (time_now - judge_stop_start_time) > 600:
							judge_move = False
							state = 'stop'
							# 写出列表里的待写出项（这些项不能算到trip里，所以把其方向改为stop)
							for str_item in stop_pending_array:
								rec = str_item.split(',')
								w_str = str(-1) + ',stop,' + rec[2] + ',' + rec[3] + ',' + rec[4] + ',' + rec[5]
								f_w.write(w_str)
							stop_pending_array = []
							#输出当前这条记录
							w_str = str(-1) + ',stop,' + str(time_now) + ',' + str(lon_now) + ',' + str(lat_now) +','+str(dis)+ '\n'
							f_w.write(w_str)
						else:
							#虽然静止，但还没满足状态条件，把待定静止的记录写到数组中
							angle = calAngle(lat_before, lon_before, lat_now, lon_now)
							w_str = str(count + len(stop_pending_array)) + ',' + str(angle) + ',' + str(time_now) + ',' + str(lon_now) + ',' + str(lat_now) + ',' + str(dis) + '\n'
							stop_pending_array.append(w_str)
					else:#开启一个stop检查周期
						judge_stop = True
						judge_stop_start_time = time_now
			line_before = line_now
			line_now = f_r.readline()  # 读新行
		f_r.close()
		f_w.close()
findDirection()

#求出租车各段trip持续时间以及每段trip方向变化次数
def findTrip():
	s = os.sep  # 根据unix或win，s为\或/
	root = r'E:' + s + 'datasets' + s + 'NewChengdu'
	dir_result = r'E:' + s + 'datasets' + s + 'NewChengdu' + s + 'direction result\\'  # 车辆方向结果
	mkdir(root + s + 'Trip Cruise\\')
	list = os.listdir(dir_result)  # 列出目录下的所有文件
	for line in list:
		#读初步统计结果（序号，行驶方向，时间）
		filename = root + s + 'direction result' + s + line
		print filename
		try:
			f_r = open(filename, 'r')
		except IOError:
			continue
		#写出二次统计结果（trip序号，cruise序号，持续时间duration）
		w_filename2 = root + s + 'Trip Cruise' + s + line
		try:
			f_w = open(w_filename2, 'w')
		except IOError:
			continue
		line_org = f_r.readline()  # 首行,调用文件的 readline()方法
		#初始状态，都认为不是处在一段trip中
		inTrip = False
		#trip的起止时间
		tripStartTime = 0
		tripEndTime = 0
		#cruise的起止时间
		cruiseStartTime = 0
		cruiseEndTime = 0
		#序号
		tripNumber = 1
		cruiseNumber = 1
		#方向角，用于cruise统计
		angle0 = 0.0
		angle1 = 0.0
		#一行行读
		while line_org:
			line = line_org.split(',')
			count = int(line[0])
			direction = line[1]#有可能是stop
			timeSec = int(line[2].split('.')[0])
			#读新行
			line_org = f_r.readline()
			if inTrip:
				if count != -1:
					dir = float(direction)
					#统计方向变化
					angle1 = dir
					if abs(angle1 - angle0) > 10:
						cruiseEndTime = timeSec#一段cruise结束了
						str_w = str(tripNumber)+','+str(cruiseNumber)+','+str( cruiseEndTime - cruiseStartTime)+','+time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(cruiseStartTime))+','+time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(cruiseEndTime))+'\n'
						f_w.write(str_w)
						#重新开始一段cruise
						cruiseNumber = cruiseNumber + 1
						angle0 = angle1
						cruiseStartTime = timeSec
					continue  # 一段trip还没有结束
				else:
					tripEndTime = timeSec#一段trip结束了
					inTrip = False
					duration = tripEndTime - tripStartTime
					#print 'duration ',duration,' tripStartTime ',time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(tripStartTime)),' tripEndTime ',time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(tripEndTime))
					#这也意味着一段cruise结束了。输出这段cruise的持续时间
					cruiseEndTime = timeSec  # 一段cruise结束了
					str_w = str(tripNumber) + ',' + str(cruiseNumber) + ',' + str( cruiseEndTime - cruiseStartTime) + ',' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cruiseStartTime)) + ',' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cruiseEndTime))+'\n'
					f_w.write(str_w)
					#接下来重新开始一段trip
					tripNumber = tripNumber + 1
					cruiseNumber = 1
					tripStartTime = timeSec
					cruiseStartTime = timeSec
			else:
				if count != -1:
					dir = float(direction)
					inTrip = True#一段trip开始了
					tripStartTime = timeSec
					cruiseStartTime = timeSec#一段trip的开始也意味着一段cruise的开始
					angle0 = dir#cruise的起始方向
				else:
					tripStartTime = timeSec
					cruiseStartTime = timeSec
					continue#保持静止
		f_r.close()
		f_w.close()

#统计行驶方向的分布情况
def dirDistribution():
	s = os.sep  # 根据unix或win，s为\或/
	#每10度一组，统计各个组别的记录条数
	means_dir = []
	for i in range(0,37):
		means_dir.append(0)
	root = r'E:' + s + 'datasets' + s + 'NewChengdu' + s + 'direction result'
	list = os.listdir(root)  # 列出目录下的所有文件
	for line in list:
		#读初步统计结果（序号，行驶方向，时间）
		filename = root + s + line
		try:
			f_r = open(filename, 'r')
		except IOError:
			continue
		print filename
		line_org = f_r.readline()  # 首行,调用文件的 readline()方法
		#一行行读
		while line_org:
			line = line_org.split(',')
			if int(line[0]) == -1:
				line_org = f_r.readline()  # 读新行
				continue
			dir = float(line[1])
			#print "dir=",dir,'   index=',(dir+180)/10
			means_dir[int((dir+180)/10)] = means_dir[int((dir+180)/10)]+1
			line_org = f_r.readline()  # 读新行
		f_r.close()

	# 统计结果写出
	w_filename2 = r'E:' + s + 'datasets' + s + 'NewChengdu' + s + 'angle_result.csv'
	try:
		f_w = open(w_filename2, 'w')
	except IOError:
		print IOError
	c = 0
	for i in range(-170,190,10):
		str_f = str(i)+','+str(means_dir[c])+'\n'
		print str_f
		f_w.write(str_f)
		c = c + 1
	f_w.close()
#将行驶方向分布统计结果绘制成图
def pltB():
	s = os.sep  # 根据unix或win，s为\或/
	n_groups = 36
	means_dir = []
	# 结果目录
	filename = r'E:' + s + 'datasets' + s + 'chengdu' + s + 'angle_result.csv'
	try:
		f_r = open(filename, 'r')
	except IOError:
		print IOError
	line_org = f_r.readline()  # 首行title 调用文件的 readline()方法
	print line_org
	# 一行行读
	while line_org:
		line = line_org.split(',')
		amount = int(line[1])
		means_dir.append(amount)
		line_org = f_r.readline()  # 读新行
	f_r.close()
	fig, ax = plt.subplots()
	index = np.arange(n_groups)
	bar_width = 0.35
	opacity = 0.4
	rects1 = plt.bar(index, means_dir, bar_width, alpha=opacity, color='b', label='Dir')
	plt.xlabel('Dir')
	plt.ylabel('Num')
	plt.title('Direction')
	m = []
	for i in range(-170, 190, 10):
		m.append(str(i))
	plt.xticks(index + bar_width, m)
	plt.legend()
	plt.tight_layout()
	plt.show()

#统计trip和crise的平均持续时间
def average():
	s = os.sep  # 根据unix或win，s为\或/
	root = r'E:' + s + 'datasets' + s + 'NewChengdu'
	tc_result = r'E:' + s + 'datasets' + s + 'NewChengdu' + s + 'Trip Cruise'  # 车辆trip和cruise结果
	#定义全局的变量：平均trip，平均cruise，trip计数，cruise计数
	trip_average = 0.0
	cruise_average = 0.0
	trip_count = 0
	cruise_count = 0
	trip_flag = 1#标记一辆车的不同trip
	trip_last_time = 0#trip持续的时间
	list = os.listdir(tc_result)  # 列出目录下的所有文件
	for line in list:
		#print line
		trip_flag = 1#当前文件的trip计数，每辆车（每个文件的trip都是从1开始编号）
		trip_last_time = 0#每个文件都要初始化trip持续时间为0
		#读tc统计结果
		filename = tc_result + s + line
		try:
			f_r = open(filename, 'r')
		except IOError:
			continue
		print filename
		line_org = f_r.readline()  # 首行,调用文件的 readline()方法
		# 一行行读
		while line_org:
			line = line_org.split(',')
			if(trip_flag != int(line[0])):
				trip_average = (trip_average * trip_count + trip_last_time)/(trip_count + 1)#结束了一段trip，更新平均trip时间
				trip_count = trip_count + 1  # 更新trip计数
				trip_flag = trip_flag + 1#更新当前文件的trip计数
				trip_last_time = 0# trip持续时间归零
			cruise_time = int(line[2])#这段cruise的持续时间
			if cruise_time > 600:
				#print filename
				#print cruise_time
				trip_last_time = trip_last_time + cruise_time#增加trip持续时间
				line_org = f_r.readline()  # 读新行
				continue
			cruise_average = (cruise_average * cruise_count + cruise_time)/(cruise_count + 1)#更新平均时间
			#print 'cruise_average = ', cruise_average,' cruise_count = ',cruise_count,' cruise_time = ',cruise_time
			cruise_count = cruise_count + 1  # 每一行都是一段cruise，每一行都要更新cruise的计数
			trip_last_time = trip_last_time + cruise_time#增加trip持续时间
			line_org = f_r.readline()  # 读新行
		#文件读完，意味着最后一段trip结束
		trip_average = (trip_average * trip_count + trip_last_time) / (trip_count + 1)  # 结束了一段trip，更新平均trip时间
		trip_count = trip_count + 1  # 更新trip计数
		f_r.close()
	print 'trip_average',trip_average
	print 'trip_count',trip_count
	print 'cruise_average',cruise_average
	print 'cruise_count',cruise_count

#首先筛选出满足时间间隔是否符合规范（60sec以内）的数据源文件
def washData():
	s = os.sep  # 根据unix或win，s为\或/
	root = r'E:' + s + 'datasets' + s + 'NewChengdu' + s + 'cabspottingdata'
	out = r'E:'+s+'VNDN'+s+'Chengdu'+s+'60sec_taxi_log_2008_by_id'
	mkdir(out)
	for i in range(1, 7000):
		filename = root + s + str(i) + '.csv'
		try:
			print filename
			f_r = open(filename, 'r')
		except IOError:
			print IOError
			continue
		# 先检查
		# 不符合规范就淘汰这个文件
		line_org = f_r.readline()  # 首行title 调用文件的 readline()方法
		count = 0
		average_gap_time = 0.0
		# 一行行读
		while line_org:
			line = line_org.split(',')
			# 时刻1
			time1 = int(line[3].split('.')[0])
			line_org = f_r.readline()  # 读新行
			# 如果新行已经是文件尾，跳出
			if not line_org:
				break
			line = line_org.split(',')
			# 时刻2
			time2 = int(line[3].split('.')[0])
			gap_time = abs(time2 - time1)
			if gap_time == 0 or gap_time > 3600:
				continue#排除掉同一时刻输出两条记录
			average_gap_time = (average_gap_time * count + gap_time) / (count + 1)
			count += 1
		print average_gap_time
		if average_gap_time > 15:
			f_r.close()
			continue  # 淘汰这个文件
		#否则把这个文件倒腾出来
		f_r.close()
		try:
			m_w = open(out + s +str(i) + '.csv', 'w')
		except IOError:
			continue
		try:
			f_r = open(filename, 'r')
		except IOError:
			continue
		line_org = f_r.readline()  # 首行title 调用文件的 readline()方法
		# 一行行读
		while line_org:
			m_w.write(line_org)
			line_org = f_r.readline()  # 读新行



#统计cruise时间的分布情况
def cruise():
	s = os.sep  # 根据unix或win，s为\或/
	#每10度一组，统计各个组别的记录条数
	cruise_time = [0]*1000
	root = r'E:' + s + 'datasets' + s + 'NewChengdu' + s + 'Trip Cruise'
	list = os.listdir(root)  # 列出目录下的所有文件
	for line in list:
		#读初步统计结果（序号，行驶方向，时间）
		filename = root + s + line
		try:
			f_r = open(filename, 'r')
		except IOError:
			continue
		print filename
		line_org = f_r.readline()  # 首行,调用文件的 readline()方法
		#一行行读
		while line_org:
			line = line_org.split(',')
			cruise = int(line[2])
			if cruise < 1000 and cruise >= 0:
				cruise_time[cruise] += 1
			line_org = f_r.readline()  # 读新行
		f_r.close()

	# 统计结果写出
	w_filename2 = r'E:' + s + 'datasets' + s + 'NewChengdu' + s + 'cruise_result.csv'
	try:
		f_w = open(w_filename2, 'w')
	except IOError:
		print IOError

	for i in range(0,1000):
		str_f = str(i)+','+str(cruise_time[i])+'\n'
		print str_f
		f_w.write(str_f)
	f_w.close()


#cruise()
#average()