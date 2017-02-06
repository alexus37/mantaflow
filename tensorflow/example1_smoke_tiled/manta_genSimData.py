
# todo, activate
#blurRealGrid( xl_density, xl_blurden, blurSig)
#newCentre = centrePosofGrid(xl_density)

from manta import *
import os, shutil, math, sys, time
import numpy as np


# Main params  ----------------------------------------------------------------------#
steps    = 200
savedata = True
simNo    = 1000  # start ID
showGui  = 1
basePath = '../data/'


steps = 50 # small test
savedata = False # debug...


# Scene settings  ---------------------------------------------------------------------#
setDebugLevel(1) 
useSavedGrid = 0 

#deal with defo
testDeform 	= 1
useDir		= False
savePatch 	= False 
saveDes 	= False
defoSubd	= 2
defoAdMode	= 2   # 2, rg = 0.5, 1, rg = 0.02, ad = 0.4
defoRgWeit	= 0.5
defoAdWeit	= 0.4
dealBad		= 99999.99

if (testDeform == 0): 	defoAdMode = 0

# Solver params  ----------------------------------------------------------------------#
lifet = steps
res   = 64
dim    = 2 
offset = 0

scaleFactor = 4
ratio       = 1.2

sm_gs = vec3(res,res,res)
xl_gs = sm_gs * float(scaleFactor)
if (dim==2):  xl_gs.z = sm_gs.z = 1  # 2D

#buoy    = vec3(0,-9e-4,0)
buoy    = vec3(0,-1e-3,0)
xl_buoy = buoy * vec3(1./scaleFactor)
velOffset    = vec3(0.)
xl_velOffset = vec3(0.)

# wlt Turbulence input fluid
sm = Solver(name='smaller', gridSize = sm_gs, dim=dim)
sm.timestep = 0.5

# wlt Turbulence output fluid
xl = Solver(name='larger', gridSize = xl_gs, dim=dim)
xl.timestep = sm.timestep 

timings = Timings()

# Insta params  -----------------------------------------------------------------------#
bgt     = 60 #60

# Simulation Grids  -------------------------------------------------------------------#
flags    = sm.create(FlagGrid)
vel      = sm.create(MACGrid)
velTmp   = sm.create(MACGrid)
density  = sm.create(RealGrid)
pressure = sm.create(RealGrid)
#energy   = sm.create(RealGrid)

xl_flags   = xl.create(FlagGrid)
xl_vel     = xl.create(MACGrid)
xl_velTmp  = xl.create(MACGrid)
xl_blurvel = xl.create(MACGrid)
xl_density = xl.create(RealGrid)
xl_blurden = xl.create(RealGrid)
xl_weight  = xl.create(RealGrid)
xl_pressure= xl.create(RealGrid)

# open boundaries
bWidth=1
flags.initDomain(boundaryWidth=bWidth)
flags.fillGrid()
xl_flags.initDomain(boundaryWidth=bWidth)
xl_flags.fillGrid()

setOpenBound(flags,    bWidth,'yY',FlagOutflow|FlagEmpty) 
setOpenBound(xl_flags, bWidth,'yY',FlagOutflow|FlagEmpty) 

# Wavelet turbulence params  ----------------------------------------------------------#
# ---- wlt Turbulence input inflow, two noise -----------------------------------------#

noises   = []
sources  = []
nseeds   = [265, 485, 672, 11, 143, 53, 320, 519, 84, 26, 398, 592]

noiseN   = len(nseeds)
cpos = vec3(0.5,0.5,0.5)

randoms = np.random.rand(noiseN, 8)
for nI in range(noiseN):
	noises.append( sm.create(NoiseField, fixedSeed=nseeds[nI], loadFromFile=True) )
	noises[nI].posScale = vec3( res * 0.1 * (randoms[nI][7] + 1) )
	noises[nI].clamp = True
	noises[nI].clampNeg = 0
	noises[nI].clampPos = 1.0
	noises[nI].valScale = 1.0
	noises[nI].valOffset = -0.01 # some gap
	noises[nI].timeAnim = 0.3
	noises[nI].posOffset = vec3(1.5)
	
	# random offsets
	coff = vec3(0.4) * (vec3( randoms[nI][0], randoms[nI][1], randoms[nI][2] ) - vec3(0.5))
	radius_rand = 0.035 + 0.035 * randoms[nI][3]
	upz = vec3(0.95)+ vec3(0.1) * vec3( randoms[nI][4], randoms[nI][5], randoms[nI][6] )
	if(dim == 2): 
		coff.z = 0.0
		upz.z = 1.0
	if( nI%2 == 0 ):
		sources.append(xl.create(Cylinder, center=xl_gs*(cpos+coff), radius=xl_gs.x*radius_rand, \
			z=xl_gs*radius_rand*upz))
	else:
		sources.append(xl.create(Sphere, center=xl_gs*(cpos+coff), radius=xl_gs.x*radius_rand, scale=upz))
		
	print (nI, "centre", xl_gs*(cpos+coff), "radius", xl_gs.x*radius_rand, "other", upz )
	
	densityInflow( flags=xl_flags, density=xl_density, noise=noises[nI], shape=sources[nI], scale=1.0, sigma=1.0 )

v1pos = vec3(0.6)
v2pos = vec3(0.35)
if(dim == 2):
	v1pos.z = v2pos.z = 0.5
velInflow = vec3(0.04, 0.01, 0)
xl_sourcV1 = xl.create(Sphere, center=xl_gs*v1pos, radius=xl_gs.x*0.1, scale=vec3(1))
xl_sourcV2 = xl.create(Sphere, center=xl_gs*v2pos, radius=xl_gs.x*0.1, scale=vec3(1))
xl_sourcV1.applyToGrid( grid=xl_vel , value=(-velInflow*float(xl_gs.x)) )
xl_sourcV2.applyToGrid( grid=xl_vel , value=(velInflow*float(xl_gs.x)) )

blurSig = float(scaleFactor) / 3.544908 # 3.544908 = 2 * sqrt( PI )
xl_blurden.copyFrom( xl_density )
#blurRealGrid( xl_density, xl_blurden, blurSig)
interpolateGrid( target=density, source=xl_blurden )

xl_blurvel.copyFrom( xl_vel )
#blurMacGrid( xl_vel, xl_blurvel, blurSig)
interpolateMACGrid( target=vel, source=xl_blurvel )
vel.multConst( vec3(1./scaleFactor) )

printBuildInfo()
# Setup UI ---------------------------------------------------------------------#
if (showGui and GUI):
	gui=Gui()
	gui.show()
	gui.pause()

# main loop
t = 0
tcnt = 0
resetN = 40

if savedata:
	folderNo = simNo
	pathaddition = 'sim_%04d/' % folderNo
	while os.path.exists(basePath + pathaddition):
		folderNo += 1
		pathaddition = 'sim_%04d/' % folderNo

	simPath = basePath + pathaddition
	simNo = folderNo
	os.makedirs(simPath)


while t < lifet+offset:
	curt = t * sm.timestep
	sys.stdout.write( "Current time t: " + str(curt) +" \n" )
	
	readFlag = ( (useSavedGrid == 1) \
		and os.path.isfile( '%ssourceVelX_%04d.uni' %(gridSavePath, t)) \
		and os.path.isfile( '%ssourceVelS_%04d.uni' %(gridSavePath, t)) \
		and os.path.isfile( '%ssourceX_%04d.uni' %(gridSavePath, t)) \
		and os.path.isfile( '%ssourceS_%04d.uni' %(gridSavePath, t)) )

	newCentre = xl_gs*float(0.5) # centrePosofGrid(xl_density)
	#print (newCentre) 
	xl_velOffset = xl_gs*float(0.5) - newCentre
	xl_velOffset = xl_velOffset * (1./ xl.timestep)
	velOffset = xl_velOffset * (1./ float(scaleFactor))
	
	#velOffset = xl_velOffset = vec3(0.0)
	if(dim == 2):
		xl_velOffset.z = velOffset.z = 0.0
	
	if (not readFlag):
		# high res fluid
		advectSemiLagrange(flags=xl_flags, vel=xl_velTmp, grid=xl_vel, order=2, openBounds=True, boundaryWidth=bWidth)
		setWallBcs(flags=xl_flags, vel=xl_vel)
		addBuoyancy(density=xl_density, vel=xl_vel, gravity=buoy , flags=xl_flags)
		if 1 and ( t< 40 ): vorticityConfinement( vel=xl_vel, flags=xl_flags, strength=0.05 )
		solvePressure(flags=xl_flags, vel=xl_vel, pressure=xl_pressure ,  cgMaxIterFac=1.0, cgAccuracy=0.01 )
		setWallBcs(flags=xl_flags, vel=xl_vel)
		xl_velTmp.copyFrom( xl_vel )
		xl_velTmp.addConst( xl_velOffset )
		if( dim == 2 ):
			xl_vel.multConst( vec3(1.0,1.0,0.0) )
			xl_velTmp.multConst( vec3(1.0,1.0,0.0) )
		advectSemiLagrange(flags=xl_flags, vel=xl_velTmp, grid=xl_density, order=2, openBounds=True, boundaryWidth=bWidth)
		xl_density.clamp(0.0, 2.0)
		# low res fluid, velocity
		if( t % resetN == 0) :
			xl_blurvel.copyFrom( xl_vel )
			#NT_DEBUG blurMacGrid( xl_vel, xl_blurvel, blurSig)
			interpolateMACGrid( target=vel, source=xl_blurvel )
			vel.multConst( vec3(1./scaleFactor) )
		else:
			advectSemiLagrange(flags=flags, vel=velTmp, grid=vel, order=2, openBounds=True, boundaryWidth=bWidth)
			setWallBcs(flags=flags, vel=vel)
			addBuoyancy(density=density, vel=vel, gravity=xl_buoy , flags=flags)
			if 1 and ( t< 40 ): vorticityConfinement( vel=vel, flags=flags, strength=0.05/scaleFactor )
			solvePressure(flags=flags, vel=vel, pressure=pressure , cgMaxIterFac=1.0, cgAccuracy=0.01 )
			setWallBcs(flags=flags, vel=vel)
		velTmp.copyFrom(vel)
		velTmp.addConst( velOffset )
		if( dim == 2 ):
			vel.multConst( vec3(1.0,1.0,0.0) )
			velTmp.multConst( vec3(1.0,1.0,0.0) )
		# low res fluid, density
		if( t % resetN == 0) :
			xl_blurden.copyFrom( xl_density )
			#NT_DEBUG blurRealGrid( xl_density, xl_blurden, blurSig)
			interpolateGrid( target=density, source=xl_blurden )
		else:
			advectSemiLagrange(flags=flags, vel=velTmp, grid=density, order=2, openBounds=True, boundaryWidth=bWidth)
			density.clamp(0.0, 2.0)
		
		# save
		if(useSavedGrid == 1):
			print("SP %s "%gridSavePath)
			xl_density.save('%ssourceX_%04d.uni' % (gridSavePath,t))
			xl_vel.save('%ssourceVelX_%04d.uni' % (gridSavePath,t))
			projectPpmFull( xl_density, '%ssourceX_%04d.ppm' % (gridSavePath,t), 0, 1.0 )
			density.save('%ssourceS_%04d.uni' % (gridSavePath,t))
			vel.save('%ssourceVelS_%04d.uni' % (gridSavePath,t))
			projectPpmFull( density, '%ssourceS_%04d.ppm' % (gridSavePath,t), 0, 1.0 )
			if( dim == 2 ):
				xl_density.save('%ssourceX_%04d.png' % (gridSavePath,t))
				density.save('%ssourceS_%04d.png' % (gridSavePath,t))
	else:
		if (t < bgt): 
			t = t + 1
			continue
		
		xl_density.load('%ssourceX_%04d.uni' % (gridSavePath,t))
		xl_vel.load('%ssourceVelX_%04d.uni' % (gridSavePath,t))
		density.load('%ssourceS_%04d.uni' % (gridSavePath,t))
		vel.load('%ssourceVelS_%04d.uni' % (gridSavePath,t))
		xl_velTmp.copyFrom( xl_vel )
		xl_velTmp.addConst( xl_velOffset )
		velTmp.copyFrom(vel)
		velTmp.addConst( velOffset )

	# save low and high res
	#if( t % resetN == (resetN-1)) :
	if 1: # save all frames
		if savedata and tcnt>=offset:
			tf = tcnt-offset
			framePath = simPath + 'frame_%04d/' % tf
			os.makedirs(framePath)
			density.save(framePath + 'density_low_%04d_%04d.uni' % (simNo, tf))
			vel.save(framePath + 'vel_low_%04d_%04d.uni' % (simNo, tf))
			xl_density.save(framePath + 'density_high_%04d_%04d.uni' % (simNo, tf))
		tcnt += 1

	sm.step()
	#gui.screenshot( 'outLibt1_%04d.png' % t )
	#timings.display()

	xl.step()
	t = t+1
