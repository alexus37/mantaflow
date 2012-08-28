/******************************************************************************
 *
 * MantaFlow fluid solver framework
 * Copyright 2011 Tobias Pfaff, Nils Thuerey 
 *
 * This program is free software, distributed under the terms of the
 * GNU General Public License (GPL) 
 * http://www.gnu.org/licenses
 *
 * FLIP (fluid implicit particles)
 *
 ******************************************************************************/

#include "flip.h"

using namespace std;
namespace Manta {

//! Set velocities from grid with given PIC/FLIP mixture
KERNEL(pts) 
CopyVelocitiesFromGrid(FlipSystem& p, FlagGrid3& flags, MACGrid3& vel, MACGrid3& oldVel, Real flipRatio) {
    if (!p.isActive(i)) return;
    
    /*if (!flags.isFluid(p[i].pos)) {
        p[i].flag |= ParticleBase::PDELETE;
        return;
    }*/
    
    Vec3 v = vel.getInterpolated(p[i].pos);
    Vec3 delta = v - oldVel.getInterpolated(p[i].pos);
    
    p[i].vel = flipRatio * (p[i].vel + delta) + (1.0f - flipRatio) * v;    
}

//! Set velocities on the grid from the particle system
KERNEL(pts, single) 
CopyVelocitiesToGrid(FlipSystem& p, FlagGrid3& flags, MACGrid3& vel, Grid3<Vec3>& tmp) {
    if (!p.isActive(i)) return;
    
    vel.setInterpolated(p[i].pos, p[i].vel, &tmp[0]);
}

void FlipSystem::velocitiesFromGrid(FlagGrid3& flags, MACGrid3& vel, Real flipRatio) {
    CopyVelocitiesFromGrid(*this, flags, vel, mOldVel, flipRatio);
}

void FlipSystem::velocitiesToGrid(FlagGrid3& flags, MACGrid3& vel) {
    // interpol -> grid. tmpgrid for counting
    Grid3<Vec3> tmp(mParent);
    vel.clear();
    CopyVelocitiesToGrid(*this, flags, vel, tmp);
    vel.safeDivide(tmp);
    
    // store diff
    mOldVel = vel;
}

void FlipSystem::adjustNumber(MACGrid3& vel, FlagGrid3& flags, int minParticles, int maxParticles) {
    Grid3<int> tmp(mParent);
    
    // count particles in cells, and delete excess particles
    for (int i=0; i<mSize; i++) {
        if (isActive(i)) {
            Vec3i p = toVec3i(mData[i].pos);
            int num = tmp(p);
            
            if (!flags.isFluid(p) || num > maxParticles)
                mData[i].flag |= PDELETE;
            else
                tmp(p) = num+1;
        }
    }
    
    compress();
    
    // seed new particles
    FOR_IJK(tmp) {
        int cnt = tmp(i,j,k);
        if (flags.isFluid(i,j,k) && cnt < minParticles) {
            for (int m=cnt; m < minParticles; m++) { 
                Vec3 rndPos (i + mRand.getReal(), j + mRand.getReal(), k + mRand.getReal());
                add(FlipData(rndPos, vel.getInterpolated(rndPos.x)));                
            }
        }
    }
}


} // namespace