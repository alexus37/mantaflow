from manta import *
import numpy as np
import matplotlib.pyplot as plt


def run():
    res = 8
    grid_sizes = vec3(res, res, 1)
    solver = Solver(name="main", gridSize=grid_sizes, dim=2)

    # prepare grids
    boundary = 0
    flags = solver.create(FlagGrid)
    flags.setConst(FlagFluid)
    flags.initDomain(boundaryWidth=boundary)
    flags.fillGrid()
    flags.printGrid()

    setOpenBound(flags, boundary, "xXyY", FlagOutflow)
    # flags.initDomain()
    # setOpenBound(flags, 10, "xXzZ", FlagFluid)
    # flags.fillGrid()
    fractions = solver.create(MACGrid)

    center = grid_sizes * vec3(0.5, 0.5, 0.5)
    radius = res * 0.25
    sphere = solver.create(Sphere, center=center, radius=radius)
    phiObs = sphere.computeLevelset()
    # not sure what this does
    # phiObs.multConst(-1)

    array_phi = np.zeros((1, int(grid_sizes.y), int(grid_sizes.x), 1))
    copyGridToArrayLevelset(source=phiObs, target=array_phi)

    updateFractions(flags=flags, phiObs=phiObs, fractions=fractions, boundaryWidth=0)

    fractions_np = np.load(f"fractions_{res}.npz")["fractions"]
    copyArrayToGridMAC(source=fractions_np, target=fractions)
    A0 = solver.create(RealGrid)
    Ai = solver.create(RealGrid)
    Aj = solver.create(RealGrid)
    Ak = solver.create(RealGrid)

    getLaplaceMatrix(flags, fractions, A0, Ai, Aj, Ak)

    array_fractions = np.zeros((1, int(grid_sizes.y), int(grid_sizes.x), 3))
    copyGridToArrayMAC(source=fractions, target=array_fractions)

    array_a0 = np.zeros((1, int(grid_sizes.y), int(grid_sizes.x), 1))
    copyGridToArrayReal(source=A0, target=array_a0)

    array_ai = np.zeros((1, int(grid_sizes.y), int(grid_sizes.x), 1))
    copyGridToArrayReal(source=Ai, target=array_ai)

    array_aj = np.zeros((1, int(grid_sizes.y), int(grid_sizes.x), 1))
    copyGridToArrayReal(source=Aj, target=array_aj)

    # print(array_a0)
    # print(array_ai)
    # print(array_aj)
    # print(array_phi)
    # print(array_ak) empty due to 2d
    np.savez(
        "/home/alelidis/Programs/manta/axtest/out.npz",
        array_a0=array_a0,
        array_ai=array_ai,
        array_aj=array_aj,
        array_phi=array_phi,
        array_fractions=array_fractions,
    )


if __name__ == "__main__":
    run()