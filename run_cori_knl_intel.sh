#!/bin/bash
module unload darshan
module swap craype-haswell craype-mic-knl
module load craype-hugepages2M
module unload cray-libsci
module load python/3.7-anaconda-2019.10
module unload cray-mpich
module swap intel intel/19.0.3.199 
export MKLROOT=/opt/intel/compilers_and_libraries_2019.3.199/linux/mkl
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/intel/compilers_and_libraries_2019.3.199/linux/mkl/lib/intel64
module load openmpi/4.0.1

export OMPI_MCA_btl_ugni_virtual_device_count=1
export PYTHONPATH=~/.local/cori/3.7-anaconda-2019.10/lib/python3.7/site-packages
export PYTHONPATH=$PYTHONPATH:$PWD/autotune/
export PYTHONPATH=$PYTHONPATH:$PWD/scikit-optimize/
export PYTHONPATH=$PYTHONPATH:$PWD/mpi4py/
# export PYTHONPATH=$PYTHONPATH:$PWD/cython/
export PYTHONPATH=$PYTHONPATH:$PWD/GPy/
export PYTHONPATH=$PYTHONPATH:$PWD/GPTune/
export PYTHONPATH=$PYTHONPATH:$PWD/examples/scalapack-driver/spt/
export PYTHONWARNINGS=ignore



CCC=mpicc
CCCPP=mpiCC
FTN=mpifort

cd examples
mpirun --mca pmix_server_max_wait 3600 --mca pmix_base_exchange_timeout 3600 --mca orte_abort_timeout 3600 --mca plm_rsh_no_tree_spawn true -n 1  python ./demo.py
# mpirun --mca pmix_server_max_wait 3600 --mca pmix_base_exchange_timeout 3600 --mca orte_abort_timeout 3600 --mca plm_rsh_no_tree_spawn true -n 1  python ./scalapack_MLA_TLA.py -mmax 1000 -nmax 1000 -nodes 1 -cores 32 -ntask 2 -nrun 10 -machine cori -jobid 0

# mpirun --mca pmix_server_max_wait 3600 --mca pmix_base_exchange_timeout 3600 --mca orte_abort_timeout 3600 --mca plm_rsh_no_tree_spawn true -n 1  python ./scalapack_TLA_loaddata.py -mmax 1000 -nmax 1000 -nodes 1 -cores 4 -ntask 2 -nrun 40 -machine cori -jobid 0

# mpirun --mca pmix_server_max_wait 3600 --mca pmix_base_exchange_timeout 3600 --mca orte_abort_timeout 3600 --mca plm_rsh_no_tree_spawn true -n 1  python ./scalapack_MLA_loaddata.py -mmax 1000 -nmax 1000 -nodes 1 -cores 4 -ntask 2 -nrun 20 -machine cori -jobid 0
# mpirun --mca pmix_server_max_wait 3600 --mca pmix_base_exchange_timeout 3600 --mca orte_abort_timeout 3600 --mca plm_rsh_no_tree_spawn true -n 1  python ./scalapack_MLA_loaddata.py -mmax 1000 -nmax 1000 -nodes 1 -cores 4 -ntask 2 -nrun 40 -machine cori -jobid 0

# mpirun --mca pmix_server_max_wait 3600 --mca pmix_base_exchange_timeout 3600 --mca orte_abort_timeout 3600 --mca plm_rsh_no_tree_spawn true -n 1  python ./superlu_MLA_TLA.py  -nodes 1 -cores 4 -ntask 1 -nrun 20 -machine cori