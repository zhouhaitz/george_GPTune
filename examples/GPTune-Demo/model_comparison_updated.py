#! /usr/bin/env python

# GPTune Copyright (c) 2019, The Regents of the University of California,
# through Lawrence Berkeley National Laboratory (subject to receipt of any
# required approvals from the U.S.Dept. of Energy) and the University of
# California, Berkeley.  All rights reserved.
#
# If you have questions about your rights to use or distribute this software,
# please contact Berkeley Lab's Intellectual Property Office at IPO@lbl.gov.
#
# NOTICE. This Software was developed under funding from the U.S. Department
# of Energy and the U.S. Government consequently retains certain rights.
# As such, the U.S. Government has been granted for itself and others acting
# on its behalf a paid-up, nonexclusive, irrevocable, worldwide license in
# the Software to reproduce, distribute copies to the public, prepare
# derivative works, and perform publicly and display publicly, and to permit
# other to do so.
#


"""
Example of invocation of this script:

mpirun -n 1 python ./demo.py -nrun 20 -ntask 5 -perfmodel 0 -optimization GPTune

where:
    -ntask is the number of different matrix sizes that will be tuned
    -nrun is the number of calls per task
    -perfmodel is whether a coarse performance model is used
    -optimization is the optimization algorithm: GPTune,opentuner,hpbandster
"""


################################################################################
import sys
import os
# import mpi4py
import logging

sys.path.insert(0, os.path.abspath(__file__ + "/../../../GPTune/"))
logging.getLogger('matplotlib.font_manager').disabled = True

from autotune.search import *
from autotune.space import *
from autotune.problem import *
from gptune import * # import all


import argparse
# from mpi4py import MPI
import numpy as np
import time
import matplotlib.pyplot as plt

from callopentuner import OpenTuner
from callhpbandster import HpBandSter



# from GPTune import *

################################################################################

# Define Problem

# YL: for the spaces, the following datatypes are supported:
# Real(lower, upper, transform="normalize", name="yourname")
# Integer(lower, upper, transform="normalize", name="yourname")
# Categoricalnorm(categories, transform="onehot", name="yourname")


# Argmin{x} objectives(t,x), for x in [0., 1.]


def parse_args():

    parser = argparse.ArgumentParser()

    parser.add_argument('-nodes', type=int, default=1,help='Number of machine nodes')
    parser.add_argument('-cores', type=int, default=2,help='Number of cores per machine node')
    parser.add_argument('-machine', type=str,default='-1', help='Name of the computer (not hostname)')
    parser.add_argument('-optimization', type=str,default='GPTune', help='Optimization algorithm (opentuner, hpbandster, GPTune)')
    parser.add_argument('-ntask', type=int, default=1, help='Number of tasks')
    parser.add_argument('-nrun', type=int, default=20, help='Number of runs per task')
    parser.add_argument('-perfmodel', type=int, default=0, help='Whether to use the performance model')
    parser.add_argument('-tvalue', type=float, default=1.0, help='Input task t value')

    args = parser.parse_args()

    return args

def objectives1(point):
    """
    f(t,x) = exp(- (x + 1) ^ (t + 1) * cos(2 * pi * x)) * (sin( (t + 2) * (2 * pi * x) ) + sin( (t + 2)^(2) * (2 * pi * x) + sin ( (t + 2)^(3) * (2 * pi *x))))
    """
    t = point['t']
    x = point['x']
    a = 2 * np.pi
    b = a * t
    c = a * x
    d = np.exp(- (x + 1) ** (t + 1)) * np.cos(c)
    e = np.sin((t + 2) * c) + np.sin((t + 2)**2 * c) + np.sin((t + 2)**3 * c)
    f = d * e + 1

    # print('test:',test)
    """
    f(t,x) = x^2+t
    """
    # t = point['t']
    # x = point['x']
    # f = 20*x**2+t
    # time.sleep(1.0)

    return [f]

def objectives2(point):
    x1 = point["x1"]
    x2 = point["x2"]
    y = 4*(x1**2) + 4*(x2**2)
    return [y]

def objectives3(point):
    x1 = point["x1"]
    x2 = point["x2"]
    x3 = point["x3"]
    x4 = point["x4"]
    x5 = point["x5"]
    x6 = point["x6"]
    y = -1*(25*((x1-2)**2) + (x2-2)**2 + (x3-1)**2 + (x4-4)**2 + (x5-1)**2 + (x6-1)**2)
    return [y]





def model_runtime(model, obj_func, NS_input,objtype,lowrank, optimizer):
    import matplotlib.pyplot as plt
    global nodes
    global cores


    # Parse command line arguments
    args = parse_args()
    ntask = args.ntask
    nrun = NS_input
    tvalue = args.tvalue
    TUNER_NAME = args.optimization
    perfmodel = args.perfmodel

    (machine, processor, nodes, cores) = GetMachineConfiguration()
    print ("machine: " + machine + " processor: " + processor + " num_nodes: " + str(nodes) + " num_cores: " + str(cores))
    os.environ['MACHINE_NAME'] = machine
    os.environ['TUNER_NAME'] = TUNER_NAME

    input_space = Space([Real(0., 10., transform="normalize", name="t")])
    # parameter_space = Space([Real(0., 1., transform="normalize", name="x")])
    
    x = Real(0., 1., transform="normalize", name="x")
    x1 = Real(0., 1., transform="normalize", name="x1")
    x2 = Real(0., 1., transform="normalize", name="x2")
    x3 = Real(0., 1., transform="normalize", name="x3")
    x4 = Real(0., 1., transform="normalize", name="x4")
    x5 = Real(0., 1., transform="normalize", name="x5")
    x6 = Real(0., 1., transform="normalize", name="x6")    
    if(objtype==1):
        parameter_space = Space([x])    
    elif(objtype==2):
        parameter_space = Space([x1,x2])    
    elif(objtype==3):
        parameter_space = Space([x1,x2,x3,x4,x5,x6])    

    # input_space = Space([Real(0., 0.0001, "uniform", "normalize", name="t")])
    # parameter_space = Space([Real(-1., 1., "uniform", "normalize", name="x")])

    output_space = Space([Real(float('-Inf'), float('Inf'), name="y")])
    #constraints = {"cst1": "x >= 0. and x <= 1."}
    constraints = {}
    if(perfmodel==1):
        problem =  (input_space, parameter_space,output_space, obj_func, constraints, models)  # with performance model
    else:
        problem = TuningProblem(input_space, parameter_space,output_space, obj_func, constraints, None)  # no performance model

    computer = Computer(nodes=nodes, cores=cores, hosts=None)
    options = Options()
    
    options['model_restarts'] = 1

    options['distributed_memory_parallelism'] = False
    options['shared_memory_parallelism'] = False

    # options['objective_evaluation_parallelism'] = True
    # options['objective_multisample_threads'] = 1
    # options['objective_multisample_processes'] = 4
    # options['objective_nprocmax'] = 1

    options['model_processes'] = 1
    # options['model_threads'] = 1
    # options['model_restart_processes'] = 1
    options['model_optimzier'] = 'lbfgs'

    # options['search_multitask_processes'] = 1
    # options['search_multitask_threads'] = 1
    # options['search_threads'] = 16

    # Use the following two lines if you want to specify a certain random seed for the random pilot sampling
    # options['sample_algo'] = 'MCS'
    options['sample_class'] = 'SampleOpenTURNS' #'SampleLHSMDU' 
    options['sample_random_seed'] = 0
    # Use the following two lines if you want to specify a certain random seed for surrogate modeling
    options['model_class'] = model #'Model_George_LCM'#'Model_George_LCM'  #'Model_LCM'
    options['model_kern'] = 'RBF' #'Matern32' #'RBF' #'Matern52'
    if(lowrank==True):
        options['model_lowrank'] = True
        options['model_hodlrleaf'] = 200
        options['model_hodlrtol'] = 1e-3
    
    # Temporary hardcode 
    if(optimizer == "gradient"):
        options['mcmc'] = False
        options['model_grad'] = True
    elif (optimizer == "mcmc"):
        options['mcmc'] = True
    elif (optimizer == "finite difference"):
        options['mcmc'] = False
        options['model_grad'] = False
    else:
        pass
        

    options['model_random_seed'] = 0
    # Use the following two lines if you want to specify a certain random seed for the search phase
    # options['search_class'] = 'SearchSciPy'
    options['search_random_seed'] = 0

    #options['search_class'] = 'SearchSciPy'
    #options['search_algo'] = 'l-bfgs-b'

    options['search_more_samples'] = 4
    options['search_af']='EI'
    # options['search_pop_size']=1000
    # options['search_ucb_beta']=0.01


    options['verbose'] = False
    options.validate(computer=computer)

    print(options)

    if ntask == 1:
        giventask = [[round(tvalue,1)]]
    elif ntask == 2:
        giventask = [[round(tvalue,1)],[round(tvalue*2.0,1)]]
    else:
        giventask = [[round(tvalue*float(i+1),1)] for i in range(ntask)]

    NI=len(giventask)
    NS=nrun

    TUNER_NAME = os.environ['TUNER_NAME']

    if(TUNER_NAME=='GPTune'):
        data = Data(problem)

        # gt = GPTune(problem, computer=computer, data=data, options=options, driverabspath=os.path.abspath(__file__)) # run GPTune with database 
        gt = GPTune(problem, computer=computer, data=data, options=options, driverabspath=os.path.abspath(__file__), historydb=False) ## Run GPTune without database

        (data, modeler, stats) = gt.MLA(NS=NS_input, NS1= int(NS_input/2.0), NI=NI, Tgiven=giventask)
#        (data, modeler, stats) = gt.MLA(NS=NS_input, NS1= int(NS_input - 1), NI=NI, Tgiven=giventask)
        print("stats: ", stats)
        """ Print all input and parameter samples """
        for tid in range(NI):
            print("tid: %d" % (tid))
            print("    t:%f " % (data.I[tid][0]))
            print("    Ps ", data.P[tid])
            print("    Os ", data.O[tid].tolist())
            print('    Popt ', data.P[tid][np.argmin(data.O[tid])], 'Oopt ', min(data.O[tid])[0], 'nth ', np.argmin(data.O[tid]))

    if(TUNER_NAME=='opentuner'):
        (data,stats)=OpenTuner(T=giventask, NS=NS, tp=problem, computer=computer, run_id="OpenTuner", niter=1, technique=None)
        print("stats: ", stats)
        """ Print all input and parameter samples """
        for tid in range(NI):
            print("tid: %d" % (tid))
            print("    t:%f " % (data.I[tid][0]))
            print("    Ps ", data.P[tid])
            print("    Os ", data.O[tid].tolist())
            print('    Popt ', data.P[tid][np.argmin(data.O[tid])], 'Oopt ', min(data.O[tid])[0], 'nth ', np.argmin(data.O[tid]))

    if(TUNER_NAME=='hpbandster'):
        (data,stats)=HpBandSter(T=giventask, NS=NS, tp=problem, computer=computer, run_id="HpBandSter", niter=1)
        print("stats: ", stats)
        """ Print all input and parameter samples """
        for tid in range(NI):
            print("tid: %d" % (tid))
            print("    t:%f " % (data.I[tid][0]))
            print("    Ps ", data.P[tid])
            print("    Os ", data.O[tid].tolist())
            print('    Popt ', data.P[tid][np.argmin(data.O[tid])], 'Oopt ', min(data.O[tid])[0], 'nth ', np.argmin(data.O[tid]))

    if(TUNER_NAME=='cgp'):
        from callcgp import cGP
        options['EXAMPLE_NAME_CGP']='GPTune-Demo'
        options['N_PILOT_CGP']=int(NS/2)
        options['N_SEQUENTIAL_CGP']=NS-options['N_PILOT_CGP']
        (data,stats)=cGP(T=giventask, tp=problem, computer=computer, options=options, run_id="cGP")
        print("stats: ", stats)
        """ Print all input and parameter samples """
        for tid in range(NI):
            print("tid: %d" % (tid))
            print("    t:%f " % (data.I[tid][0]))
            print("    Ps ", data.P[tid])
            print("    Os ", data.O[tid].tolist())
            print('    Popt ', data.P[tid][np.argmin(data.O[tid])], 'Oopt ', min(data.O[tid])[0], 'nth ', np.argmin(data.O[tid]))
    
    return stats


def objective_selection():
    objective = input("What Objective Function would you like to use (1, 2, or 3)")
    if ("1" in objective):
        objtype=1
        return objectives1, objtype
    elif ("2" in objective):
        objtype=2
        return objectives2, objtype
    elif ("3" in objective):
        objtype=3
        return objectives3, objtype
    else:
        raise Exception("Invalid objective selection")

    
# def setup():
#     # setup cases base off input

#     # Have the option to select the kernel for each 

#     objective = input("How many many cases would you like compare?")



    
    
import matplotlib.pyplot as plt

def plotting(objective, objtype):
    model_time_gpy = []
    model_time_per_likelihoodeval_gpy = []
    search_time_gpy = []
    model_iterations_gpy = []

    model_time_george_hodlr_gradient = []
    model_time_per_likelihoodeval_george_hodlr_gradient = []
    search_time_george_hodlr_gradient = []
    model_iterations_hodlr_gradient = []

    model_time_george_hodlr_finite_difference = []
    model_time_per_likelihoodeval_george_hodlr_finite_difference = []
    search_time_george_hodlr_finite_difference = []
    model_iterations_hodlr_finite_difference = []

    model_time_george_hodlr_mcmc = []
    model_time_per_likelihoodeval_george_hodlr_mcmc = []
    search_time_george_hodlr_mcmc = []
    model_iterations_hodlr_mcmc = []



    NS = [201]
    
    for elem in NS:
        # hodlr_stats_gradient = model_runtime(model="Model_George", obj_func=objective, NS_input=elem, objtype=objtype, lowrank=True, optimizer="gradient")
        # model_time_george_hodlr_gradient.append(hodlr_stats_gradient.get("time_model"))
        # model_time_per_likelihoodeval_george_hodlr_gradient.append(hodlr_stats_gradient.get("time_model_per_likelihoodeval"))
        # search_time_george_hodlr_gradient.append(hodlr_stats_gradient.get("time_search"))
        # model_iterations_hodlr_gradient.extend(hodlr_stats_gradient.get("modeling_iteration"))
        

        # hodlr_stats_finite_difference = model_runtime(model="Model_George", obj_func=objective, NS_input=elem, objtype=objtype, lowrank=True, optimizer = "finite difference")
        # model_time_george_hodlr_finite_difference.append(hodlr_stats_finite_difference.get("time_model"))
        # model_time_per_likelihoodeval_george_hodlr_finite_difference.append(hodlr_stats_finite_difference.get("time_model_per_likelihoodeval"))
        # search_time_george_hodlr_finite_difference.append(hodlr_stats_finite_difference.get("time_search"))
        # model_iterations_hodlr_finite_difference.extend(hodlr_stats_finite_difference.get("modeling_iteration"))

        hodlr_stats_mcmc = model_runtime(model="Model_George", obj_func=objective, NS_input=elem, objtype=objtype, lowrank=True, optimizer="mcmc")
        model_time_george_hodlr_mcmc.append(hodlr_stats_mcmc.get("time_model"))
        model_time_per_likelihoodeval_george_hodlr_mcmc.append(hodlr_stats_mcmc.get("time_model_per_likelihoodeval"))
        search_time_george_hodlr_mcmc.append(hodlr_stats_mcmc.get("time_search"))
        model_iterations_hodlr_mcmc.extend(hodlr_stats_mcmc.get("modeling_iteration"))


        gpy_stats = model_runtime(model="Model_GPy_LCM", obj_func=objective, NS_input=elem, objtype=objtype, lowrank=False, optimizer = "Gpy_optimizer") 
        model_time_gpy.append(gpy_stats.get("time_model"))
        model_time_per_likelihoodeval_gpy.append(gpy_stats.get("time_model_per_likelihoodeval"))
        search_time_gpy.append(gpy_stats.get("time_search"))
        model_iterations_gpy.extend(gpy_stats.get("modeling_iteration"))
     
    


    # Model Time
    print("Time-Model George HODLR Gradient: ", model_time_george_hodlr_gradient)
    print("Time-Model George HODLR Finite Difference: ", model_time_george_hodlr_finite_difference)
    print("Time-Model George HODLR MCMC: ", model_time_george_hodlr_mcmc)
    print("Time-Model GPy: ", model_time_gpy)

    # Search Time
    print("Time-Search George HODLR Gradient: ", search_time_george_hodlr_gradient)
    print("Time-Search George HODLR Finite Difference: ", search_time_george_hodlr_finite_difference)
    print("Time-Search George HODLR MCMC: ", search_time_george_hodlr_mcmc)
    print("Time-Search GPy: ", search_time_gpy)

    # Inversion Time
    print("Inversion Time George HODLR Gradient: ", model_time_per_likelihoodeval_george_hodlr_gradient)
    print("Inversion Time George HODLR Finite Difference: ", model_time_per_likelihoodeval_george_hodlr_finite_difference)
    print("Inversion Time George HODLR MCMC: ", model_time_per_likelihoodeval_george_hodlr_mcmc)
    print("Inversion Time GPy: ", model_time_per_likelihoodeval_gpy)

    # Modeling Iterations
    print("Modeling Iterations George HODLR Gradient: ", model_iterations_hodlr_gradient)
    print("Modeling Iterations George HODLR Finite Difference: ", model_iterations_hodlr_finite_difference)
    print("Modeling Iterations George HODLR MCMC: ", model_iterations_hodlr_mcmc)
    print("Modeling Iterations GPy: ", model_iterations_gpy)



    figure, axis = plt.subplots(2,2)
    figure.suptitle("Optimizer Comparison 1D")

    axis[0,0].loglog(NS, model_time_gpy, label="GPy", color="green", marker='o')
    axis[0,0].loglog(NS, model_time_george_hodlr_gradient, label="george_hodlr_gradient", color="blue", marker='o')
    axis[0,0].loglog(NS, model_time_george_hodlr_finite_difference, label="george_hodlr_finite_difference", color="red", marker='o')
    axis[0,0].loglog(NS, model_time_george_hodlr_mcmc, label="george_hodlr_mcmc", color="purple", marker='o')
    axis[0,0].legend()
    axis[0,0].set_title("Model Time Comparison")
    axis[0,0].set_xlabel("Number of Samples")
    axis[0,0].set_ylabel("Time (sec)")

    axis[0,1].loglog(NS, search_time_gpy, label="GPy", color="green", marker='o')
    axis[0,1].loglog(NS, search_time_george_hodlr_gradient, label="george_hodlr_gradient", color="blue", marker='o')
    axis[0,1].loglog(NS, search_time_george_hodlr_finite_difference, label="george_hodlr_finite_difference", color="red", marker='o')
    axis[0,1].loglog(NS, search_time_george_hodlr_mcmc, label="george_hodlr_mcmc", color="purple", marker='o')
    axis[0,1].legend()
    axis[0,1].set_title("Search Time Comparison")
    axis[0,1].set_xlabel("Number of Samples")
    axis[0,1].set_ylabel("Time (sec)")

    axis[1,0].loglog(NS, model_time_per_likelihoodeval_gpy, label="GPy", color="green", marker='o')
    axis[1,0].loglog(NS, model_time_per_likelihoodeval_george_hodlr_gradient, label="george_hodlr_gradient", color="blue", marker='o')
    axis[1,0].loglog(NS, model_time_per_likelihoodeval_george_hodlr_finite_difference, label="george_hodlr_finite_difference", color="red", marker='o')
    axis[1,0].loglog(NS, model_time_per_likelihoodeval_george_hodlr_mcmc, label="george_hodlr_mcmc", color="purple", marker='o')
    axis[1,0].legend()
    axis[1,0].set_title("Model Covariance Inversion Time Comparison")
    axis[1,0].set_xlabel("Number of Samples")
    axis[1,0].set_ylabel("Time (sec)")

    axis[1,1].plot(NS, model_iterations_gpy, label="GPy", color="green", marker='o')
    axis[1,1].plot(NS, model_iterations_hodlr_gradient, label="george_hodlr_gradient", color="blue", marker='o')
    axis[1,1].plot(NS, model_iterations_hodlr_finite_difference, label="george_hodlr_finite_difference", color="red", marker='o')
    axis[1,1].plot(NS, model_iterations_hodlr_mcmc, label="george_hodlr_mcmc", color="purple", marker='o')
    axis[1,1].legend()
    axis[1,1].set_title("Model Iterations Comparison")
    axis[1,1].set_xlabel("Number of Samples")
    axis[1,1].set_ylabel("Iterations")






    plt.tight_layout()
    plt.show()
    plt.savefig('opttimizer_compare.pdf')

def main():
    objective, objtype = objective_selection()
    plotting(objective=objective, objtype=objtype)




if __name__ == "__main__":
    main()

