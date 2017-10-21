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

#样本数据集包含10000+辆成都出租车的行驶轨迹记录，每两次采样的时间间隔约为10~30sec
#求各时刻出租车的行驶方向，这里需要格外注意相邻两时刻坐标相同的情况，这意味着车辆静止，是一段trip结束的标志
def direction1():
	s = os.sep  # 根据unix或win，s为\或/
	root = r'E:' + s + 'datasets' + s + 'NewChengdu' + s + 'cabspottingdata'#这辆车的所有记录都存在这个文件夹下
	dir_result = r'E:' + s + 'datasets' + s + 'NewChengdu' + s + 'direction result\\'#保存车辆个各时刻的方向
	mkdir(dir_result)#结果存到这个文件夹下
	list = os.listdir(root)  # 列出记录目录下的所有文件

	for line in list:
		print line
		filename = root+s+line
		try:
			f_r = open(filename, 'r')
		except IOError:
			continue
		# 行驶方向结果写出
		w_filename = dir_result + s + line.split('.')[0] + '.csv'
		try:
			f_w = open(w_filename, 'w')
		except IOError:
			continue
		line_org = f_r.readline()  # 首行title 调用文件的 readline()方法
		count = 1
		# 一行行读
		while line_org:
			line = line_org.split(',')
			# 时刻1坐标
			lon1 = float(line[2])
			lat1 = float(line[1])
			#记录时间
			timeSec = line[3]
			line_org = f_r.readline()  # 读新行
			# 如果新行已经是文件尾，跳出
			if not line_org:
				break
			line = line_org.split(',')
			# 时刻2坐标
			lon2 = float(line[2])
			lat2 = float(line[1])
			# 如果两点重合，额外标注
			if lon1 == lon2 and lat1 == lat2:
				w_str = '-1,stop,' + timeSec
				f_w.write(w_str)
				continue
			angle = calAngle2(lat1, lon1, lat2, lon2)
			w_str = str(count) + ',' + str(angle) + ',' + timeSec
			#print w_str
			#print lat1, lon1, lat2, lon2
			f_w.write(w_str)
			count = count + 1
		f_r.close()
		f_w.close()

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
average()