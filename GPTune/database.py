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

import numpy as np
from problem import Problem
from data import Data
import json
import os.path
from filelock import FileLock
from autotune.space import *
from autotune.problem import TuningProblem
import uuid
import time

def GetMachineConfiguration(meta_description_path = "./.gptune/meta.json"):
    import ast

    # machine configuration values
    machine_name = "mymachine"
    processor_model = "unknown"
    nodes = 1
    cores = 2

    if (os.environ.get('CKGPTUNE_HISTORY_DB') == 'yes'):
        try:
            machine_configuration = ast.literal_eval(os.environ.get('CKGPTUNE_MACHINE_CONFIGURATION', '{}'))
            machine_name = machine_configuration['machine_name']
            processor_list = list(machine_configuration.keys())
            processor_list.remove('machine_name')
            # YC: we currently assume the application uses only one processor type
            processor_model = processor_list[0]
            nodes = machine_configuration[processor_model]['nodes']
            cores = machine_configuration[processor_model]['cores']
        except:
            print ("[HistoryDB] not able to get machine configuration")

    elif os.path.exists(meta_description_path):
        try:
            with open(meta_description_path) as f_in:
                gptune_metadata = json.load(f_in)
                machine_configuration = gptune_metadata['machine_configuration']
                machine_name = machine_configuration['machine_name']
                processor_list = list(machine_configuration.keys())
                processor_list.remove('machine_name')
                # YC: we currently assume the application uses only one processor type
                processor_model = processor_list[0]
                nodes = machine_configuration[processor_model]['nodes']
                cores = machine_configuration[processor_model]['cores']
        except:
            print ("[HistoryDB] not able to get machine configuration")

    else:
        print ("[HistoryDB] not able to get machine configuration")

    #return (machine_configuration)
    return (machine_name, processor_model, nodes, cores)

def GetMachineConfigurationDict(meta_description_path = "./.gptune/meta.json"):
    import ast

    machine_configuration = {}

    if (os.environ.get('CKGPTUNE_HISTORY_DB') == 'yes'):
        try:
            machine_configuration = ast.literal_eval(os.environ.get('CKGPTUNE_MACHINE_CONFIGURATION', '{}'))
        except:
            print ("[HistoryDB] not able to get machine configuration")

    elif os.path.exists(meta_description_path):
        try:
            with open(meta_description_path) as f_in:
                gptune_metadata = json.load(f_in)
                machine_configuration = gptune_metadata['machine_configuration']
        except:
            print ("[HistoryDB] not able to get machine configuration")

    else:
        print ("[HistoryDB] not able to get machine configuration")

    return (machine_configuration)

def GetSoftwareConfigurationDict(meta_description_path = "./.gptune/meta.json"):
    import ast

    software_configuration = {}

    if (os.environ.get('CKGPTUNE_HISTORY_DB') == 'yes'):
        try:
            software_configuration = ast.literal_eval(os.environ.get('CKGPTUNE_SOFTWARE_CONFIGURATION', '{}'))
        except:
            print ("[HistoryDB] not able to get software configuration")

    elif os.path.exists(meta_description_path):
        try:
            with open(meta_description_path) as f_in:
                gptune_metadata = json.load(f_in)
                software_configuration = gptune_metadata['software_configuration']
        except:
            print ("[HistoryDB] not able to get software configuration")

    else:
        print ("[HistoryDB] not able to get software configuration")

    return (software_configuration)

def search_item_by_uid(dict_arr, uid):

    for item in dict_arr:
        if (item["uid"] == uid):
            return item

    return None

class HistoryDB(dict):

    def __init__(self, **kwargs):

        self.tuning_problem_name = None

        """ Options """
        self.history_db = True
        self.save_func_eval = True
        self.save_model = True
        self.load_func_eval = True
        self.load_surrogate_model = False

        """ Path to JSON data files """
        self.history_db_path = "./"

        """ Pass machine-related information """
        self.machine_configuration = {
                    "machine":"Unknown",
                    "nodes":"Unknown",
                    "cores":"Unknown"
                }

        """ Pass software-related information """
        self.software_configuration = {}

        """ Loadable machine configurations """
        self.loadable_machine_configurations = {}

        """ Loadable software configurations """
        self.loadable_software_configurations = {}

        """ Verbose debug message """
        self.verbose = 1

        """ list of UIDs of function evaluation results """
        self.uids = []

        """ File synchronization options """
        self.file_synchronization_method = 'filelock'

        """ Process uid """
        self.process_uid = str(uuid.uuid1())

        # if history database is requested by CK-GPTune
        if (os.environ.get('CKGPTUNE_HISTORY_DB') == 'yes'):
            print ("CK-GPTune History Database Init")
            import ast
            self.tuning_problem_name = os.environ.get('CKGPTUNE_TUNING_PROBLEM_NAME','Unknown')
            self.machine_configuration = ast.literal_eval(os.environ.get('CKGPTUNE_MACHINE_CONFIGURATION','{}'))

            software_configuration = ast.literal_eval(os.environ.get('CKGPTUNE_SOFTWARE_CONFIGURATION','{}'))
            for x in software_configuration:
                self.software_configuration[x] = software_configuration[x]
            compile_deps = ast.literal_eval(os.environ.get('CKGPTUNE_COMPILE_DEPS','{}'))
            for x in compile_deps:
                self.software_configuration[x] = compile_deps[x]
            runtime_deps = ast.literal_eval(os.environ.get('CKGPTUNE_RUNTIME_DEPS','{}'))
            for x in runtime_deps:
                self.software_configuration[x] = runtime_deps[x]

            self.loadable_machine_configurations = ast.literal_eval(os.environ.get('CKGPTUNE_LOADABLE_MACHINE_CONFIGURATIONS','{}'))
            self.loadable_software_configurations = ast.literal_eval(os.environ.get('CKGPTUNE_LOADABLE_SOFTWARE_CONFIGURATIONS', '{}'))

            os.system("mkdir -p ./gptune.db")
            self.history_db_path = "./gptune.db"

            if (os.environ.get('CKGPTUNE_LOAD_MODEL') == 'yes'):
                self.load_surrogate_model = True
            try:
                with FileLock("test.lock", timeout=0):
                    print ("[HistoryDB] use filelock for synchronization")
                    self.file_synchronization_method = 'filelock'
            except:
                print ("[HistoryDB] use rsync for synchronization")
                self.file_synchronization_method = 'rsync'
            os.system("rm -rf test.lock")

        # if GPTune is called through Reverse Communication Interface
        elif os.path.exists('./.gptune/meta.json'): #or (os.environ.get('GPTUNE_RCI') == 'yes'):
            with open("./.gptune/meta.json") as f_in:
                print ("GPTune History Database Init")

                gptune_metadata = json.load(f_in)

                if "tuning_problem_name" in gptune_metadata:
                    self.tuning_problem_name = gptune_metadata["tuning_problem_name"]
                else:
                    self.tuning_problem_name = "Unknown"

                if "history_db_path" in gptune_metadata:
                    self.history_db_path = gptune_metadata["history_db_path"]
                else:
                    os.system("mkdir -p ./gptune.db")
                    self.history_db_path = "./gptune.db"

                if "machine_configuration" in gptune_metadata:
                    self.machine_configuration = gptune_metadata["machine_configuration"]
                if "software_configuration" in gptune_metadata:
                    self.software_configuration = gptune_metadata["software_configuration"]
                if "loadable_machine_configurations" in gptune_metadata:
                    self.loadable_machine_configurations = gptune_metadata["loadable_machine_configurations"]
                if "loadable_software_configurations" in gptune_metadata:
                    self.loadable_software_configurations = gptune_metadata["loadable_software_configurations"]

                try:
                    with FileLock("test.lock", timeout=0):
                        print ("[HistoryDB] use filelock for synchronization")
                        self.file_synchronization_method = 'filelock'
                except:
                    print ("[HistoryDB] use rsync for synchronization")
                    self.file_synchronization_method = 'rsync'
                os.system("rm -rf test.lock")
        else:
            self.history_db = False

    def check_load_deps(self, func_eval):

        ''' check machine configuration dependencies '''
        loadable_machine_configurations = self.loadable_machine_configurations
        machine_configuration = func_eval['machine_configuration']
        machine_name = machine_configuration['machine_name']
        processor_list = list(machine_configuration.keys())
        processor_list.remove("machine_name")
        if not machine_name in loadable_machine_configurations.keys():
            print (machine_name+": " + machine_name + " is not in load_deps: " + str(loadable_machine_configurations.keys()))
            return False
        else:
            for processor in processor_list:
                if not processor in loadable_machine_configurations[machine_name]:
                    return False
                else:
                    num_nodes = machine_configuration[processor]["nodes"]
                    num_nodes_loadable = loadable_machine_configurations[machine_name][processor]["nodes"]
                    if type(num_nodes_loadable) == list:
                        if num_nodes not in num_nodes_loadable:
                            return False
                    elif type(num_nodes_loadable) == int:
                        if num_nodes != num_nodes_loadable:
                            return False
                    else:
                        return False

                    num_cores = machine_configuration[processor]["cores"]
                    num_cores_loadable = loadable_machine_configurations[machine_name][processor]["cores"]
                    if type(num_cores_loadable) == list:
                        if num_cores not in num_cores_loadable:
                            return False
                    elif type(num_cores_loadable) == int:
                        if num_cores != num_cores_loadable:
                            return False
                    else:
                        return False

        ''' check compile-level software dependencies '''
        loadable_software_configurations = self.loadable_software_configurations
        software_configuration = func_eval['software_configuration']
        for software_name in loadable_software_configurations.keys():
            deps_passed = False

            #software_name = loadable_software_configurations[software_name][option]['name']
            if software_name in software_configuration.keys():
                version_split = software_configuration[software_name]['version_split']
                version_value = version_split[0]*100+version_split[1]*10+version_split[2]
                #print ("software_name: " + software_name + " version_value: " + str(version_value))

                if 'version_split' in loadable_software_configurations[software_name].keys():
                    version_dep_split = loadable_software_configurations[software_name]['version_split']
                    version_dep_value = version_dep_split[0]*100+version_dep_split[1]*10+version_dep_split[2]

                    if version_dep_value == version_value:
                        deps_passed = True

                if 'version_from' in loadable_software_configurations[software_name].keys() and \
                   'version_to' not in loadable_software_configurations[software_name].keys():
                    version_dep_from_split = loadable_software_configurations[software_name]['version_from']
                    version_dep_from_value = version_dep_from_split[0]*100+version_dep_from_split[1]*10+version_dep_from_split[2]

                    if version_dep_from_value <= version_value:
                        deps_passed = True

                if 'version_from' not in loadable_software_configurations[software_name].keys() and \
                   'version_to' in loadable_software_configurations[software_name].keys():
                    version_dep_to_split = loadable_software_configurations[software_name]['version_to']
                    version_dep_to_value = version_dep_to_split[0]*100+version_dep_to_split[1]*10+version_dep_to_split[2]

                    if version_dep_to_value >= version_value:
                        deps_passed = True

                if 'version_from' in loadable_software_configurations[software_name].keys() and \
                   'version_to' in loadable_software_configurations[software_name].keys():
                    version_dep_from_split = loadable_software_configurations[software_name]['version_from']
                    version_dep_from_value = version_dep_from_split[0]*100+version_dep_from_split[1]*10+version_dep_from_split[2]

                    version_dep_to_split = loadable_software_configurations[software_name]['version_to']
                    version_dep_to_value = version_dep_to_split[0]*100+version_dep_to_split[1]*10+version_dep_to_split[2]

                    if version_dep_from_value <= version_value and \
                       version_dep_to_value >= version_value:
                        deps_passed = True

            if (deps_passed == False):
                if (self.verbose):
                    print ("deps_passed failed: "  + " " + str(software_name)) 
                return False

        return True

    def search_func_eval_task_id(self, func_eval : dict, problem : Problem, Igiven : np.ndarray):
        task_id = -1

        for i in range(len(Igiven)):
            compare_all_elems = True
            for j in range(len(problem.IS)):
                if (func_eval["task_parameter"][problem.IS[j].name] != Igiven[i][j]):
                    compare_all_elems = False
                    break
            if compare_all_elems == True:
                task_id = i
                break

        return task_id

    def is_parameter_duplication(self, problem : Problem, PS_history, parameter):
        # for i in range(len(PS_history)):
        for j in range(len(PS_history)):
            compare_all_elems = True
            for k in range(len(problem.PS)):
                if (parameter[problem.PS[k].name] != PS_history[j][k]):
                    compare_all_elems = False
                    break
            if compare_all_elems == True:
                print ("found a duplication of parameter set: ", parameter)
                return True

        return False

    def load_history_func_eval(self, data : Data, problem : Problem, Igiven : np.ndarray):
        """ Init history database JSON file """
        if (self.tuning_problem_name is not None):
            json_data_path = self.history_db_path+"/"+self.tuning_problem_name+".json"
            if os.path.exists(json_data_path):
                print ("[HistoryDB] Found a history database file")
                if self.file_synchronization_method == 'filelock':
                    with FileLock(json_data_path+".lock"):
                        with open(json_data_path, "r") as f_in:
                            history_data = json.load(f_in)
                elif self.file_synchronization_method == 'rsync':
                    temp_path = json_data_path + "." + self.process_uid + ".temp"
                    os.system("rsync -a " + json_data_path + " " + temp_path)
                    with open(temp_path, "r") as f_in:
                        history_data = json.load(f_in)
                    os.system("rm " + temp_path)
                else:
                    with open(json_data_path, "r") as f_in:
                        history_data = json.load(f_in)

                num_tasks = len(Igiven)

                num_loaded_data = 0

                PS_history = [[] for i in range(num_tasks)]
                OS_history = [[] for i in range(num_tasks)]

                for func_eval in history_data["func_eval"]:
                    if (self.check_load_deps(func_eval)):
                        task_id = self.search_func_eval_task_id(func_eval, problem, Igiven)
                        if (task_id != -1):
                            # # current policy: skip loading the func eval result
                            # # if the same parameter data has been loaded once (duplicated)
                            # # YL: only need to search in PS_history[task_id], not PS_history
                            # if self.is_parameter_duplication(problem, PS_history[task_id], func_eval["tuning_parameter"]):
                            
                            # current policy: allow duplicated samples 
                            # YL: This makes RCI-based multi-armed bandit much easier to implement, maybe we can add an option for changing this behavior 
                            if False: # self.is_parameter_duplication(problem, PS_history[task_id], func_eval["tuning_parameter"]):
                                continue
                            else:
                                parameter_arr = []
                                for k in range(len(problem.PS)):
                                    if type(problem.PS[k]).__name__ == "Categoricalnorm":
                                        parameter_arr.append(str(func_eval["tuning_parameter"][problem.PS[k].name]))
                                    elif type(problem.PS[k]).__name__ == "Integer":
                                        parameter_arr.append(int(func_eval["tuning_parameter"][problem.PS[k].name]))
                                    elif type(problem.PS[k]).__name__ == "Real":
                                        parameter_arr.append(float(func_eval["tuning_parameter"][problem.PS[k].name]))
                                    else:
                                        parameter_arr.append(func_eval["tuning_parameter"][problem.PS[k].name])
                                PS_history[task_id].append(parameter_arr)
                                OS_history[task_id].append(\
                                    [func_eval["evaluation_result"][problem.OS[k].name] \
                                    for k in range(len(problem.OS))])
                                num_loaded_data += 1

                if (num_loaded_data > 0):
                    data.I = Igiven #IS_history
                    data.P = PS_history
                    data.O=[] # YL: OS is a list of 2D numpy arrays
                    for i in range(len(OS_history)):
                        if(len(OS_history[i])==0):
                            data.O.append(np.empty( shape=(0, problem.DO)))
                        else:
                            data.O.append(np.array(OS_history[i]))
                            if(any(ele==[None] for ele in OS_history[i])):
                                print ("history data contains null function values")
                                exit()
                    # print ("db: data.I: " + str(data.I))
                    # print ("db: data.P: " + str(data.P))
                    # print ("db: data.O: " + str(OS_history))
                else:
                    print ("no history data has been loaded")
            else:
                print ("[HistoryDB] Create a JSON file at " + json_data_path)

                if self.file_synchronization_method == 'filelock':
                    with FileLock(json_data_path+".lock"):
                        with open(json_data_path, "w") as f_out:
                            json_data = {"tuning_problem_name":self.tuning_problem_name,
                                "surrogate_model":[],
                                "func_eval":[]}
                            json.dump(json_data, f_out, indent=2)
                elif self.file_synchronization_method == 'rsync':
                    temp_path = json_data_path + "." + self.process_uid + ".temp"
                    with open(temp_path, "w") as f_out:
                        json_data = {"tuning_problem_name":self.tuning_problem_name,
                            "surrogate_model":[],
                            "func_eval":[]}
                        json.dump(json_data, f_out, indent=2)
                    os.system("rsync -u " + temp_path + " " + json_data_path)
                    os.system("rm " + temp_path)
                else:
                    with open(json_data_path, "w") as f_out:
                        json_data = {"tuning_problem_name":self.tuning_problem_name,
                            "surrogate_model":[],
                            "func_eval":[]}
                        json.dump(json_data, f_out, indent=2)

    def load_model_func_eval(self, data : Data, problem : Problem, Igiven : np.ndarray, model_data : dict):
        """ Init history database JSON file """
        if (self.tuning_problem_name is not None):
            json_data_path = self.history_db_path+"/"+self.tuning_problem_name+".json"
            if os.path.exists(json_data_path):
                print ("[HistoryDB] Found a history database file")
                if self.file_synchronization_method == 'filelock':
                    with FileLock(json_data_path+".lock"):
                        with open(json_data_path, "r") as f_in:
                            history_data = json.load(f_in)
                elif self.file_synchronization_method == 'rsync':
                    temp_path = json_data_path + "." + self.process_uid + ".temp"
                    os.system("rsync -a " + json_data_path + " " + temp_path)
                    with open(temp_path, "r") as f_in:
                        history_data = json.load(f_in)
                    os.system("rm " + temp_path)
                else:
                    with open(json_data_path, "r") as f_in:
                        history_data = json.load(f_in)

                num_tasks = len(Igiven)

                num_loaded_data = 0

                PS_history = [[] for i in range(num_tasks)]
                OS_history = [[] for i in range(num_tasks)]

                # Assume that all function evaluations of the surrogate model are in the database file
                for func_eval_uid in model_data["function_evaluations"]:
                    func_eval = search_item_by_uid(history_data["func_eval"], func_eval_uid)
                    parameter_arr = []
                    for k in range(len(problem.PS)):
                        if type(problem.PS[k]).__name__ == "Categoricalnorm":
                            parameter_arr.append(str(func_eval["tuning_parameter"][problem.PS[k].name]))
                        elif type(problem.PS[k]).__name__ == "Integer":
                            parameter_arr.append(int(func_eval["tuning_parameter"][problem.PS[k].name]))
                        elif type(problem.PS[k]).__name__ == "Real":
                            parameter_arr.append(float(func_eval["tuning_parameter"][problem.PS[k].name]))
                        else:
                            parameter_arr.append(func_eval["tuning_parameter"][problem.PS[k].name])
                    task_id = self.search_func_eval_task_id(func_eval, problem, Igiven)
                    PS_history[task_id].append(parameter_arr)
                    OS_history[task_id].append(\
                        [func_eval["evaluation_result"][problem.OS[k].name] \
                        for k in range(len(problem.OS))])
                    num_loaded_data += 1

                if (num_loaded_data > 0):
                    data.I = Igiven #IS_history
                    data.P = PS_history
                    data.O=[] # YL: OS is a list of 2D numpy arrays
                    for i in range(len(OS_history)):
                        if(len(OS_history[i])==0):
                            data.O.append(np.empty( shape=(0, problem.DO)))
                        else:
                            data.O.append(np.array(OS_history[i]))
                            if(any(ele==[None] for ele in OS_history[i])):
                                print ("history data contains null function values")
                                exit()
                else:
                    print ("no history data has been loaded")
            else:
                print ("[HistoryDB] Create a JSON file at " + json_data_path)

                if self.file_synchronization_method == 'filelock':
                    with FileLock(json_data_path+".lock"):
                        with open(json_data_path, "w") as f_out:
                            json_data = {"tuning_problem_name":self.tuning_problem_name,
                                "surrogate_model":[],
                                "func_eval":[]}
                            json.dump(json_data, f_out, indent=2)
                elif self.file_synchronization_method == 'rsync':
                    temp_path = json_data_path + "." + self.process_uid + ".temp"
                    with open(temp_path, "w") as f_out:
                        json_data = {"tuning_problem_name":self.tuning_problem_name,
                            "surrogate_model":[],
                            "func_eval":[]}
                        json.dump(json_data, f_out, indent=2)
                    os.system("rsync -u " + temp_path + " " + json_data_path)
                    os.system("rm " + temp_path)
                else:
                    with open(json_data_path, "w") as f_out:
                        json_data = {"tuning_problem_name":self.tuning_problem_name,
                            "surrogate_model":[],
                            "func_eval":[]}
                        json.dump(json_data, f_out, indent=2)

    def store_func_eval(self, problem : Problem,\
            task_parameter : np.ndarray,\
            tuning_parameter : np.ndarray,\
            evaluation_result : np.ndarray,\
            source : str = "measure"):

        print ("store_func_eval")
        print ("problem.constants")
        print (problem.constants)

        if (self.tuning_problem_name is not None):
            json_data_path = self.history_db_path+"/"+self.tuning_problem_name+".json"

            new_function_evaluation_results = []

            now = time.localtime()

            # get the types of each parameter
            task_dtype=''
            for p in problem.IS.dimensions:
                if (isinstance(p, Real)):
                    task_dtype=task_dtype+', float64'
                elif (isinstance(p, Integer)):
                    task_dtype=task_dtype+', int32'
                elif (isinstance(p, Categorical)):
                    task_dtype=task_dtype+', U100'
            task_dtype=task_dtype[2:]
            
            tuning_dtype=''
            for p in problem.PS.dimensions:
                if (isinstance(p, Real)):
                    tuning_dtype=tuning_dtype+', float64'
                elif (isinstance(p, Integer)):
                    tuning_dtype=tuning_dtype+', int32'
                elif (isinstance(p, Categorical)):
                    tuning_dtype=tuning_dtype+', U100'
            tuning_dtype=tuning_dtype[2:]

            # transform to the original parameter space
            task_parameter_orig = problem.IS.inverse_transform(np.array(task_parameter, ndmin=2))[0]
            task_parameter_orig_list = np.array(tuple(task_parameter_orig),dtype=task_dtype).tolist()

            num_evals = len(tuning_parameter)
            for i in range(num_evals):
                uid = uuid.uuid1()
                self.uids.append(str(uid))

                tuning_parameter_orig = problem.PS.inverse_transform(
                        np.array(tuning_parameter[i], ndmin=2))[0]
                tuning_parameter_orig_list = np.array(tuple(tuning_parameter_orig),dtype=tuning_dtype).tolist()
                evaluation_result_orig_list = np.array(evaluation_result[i]).tolist()

                task_parameter_store = { problem.IS[k].name:task_parameter_orig_list[k] for k in range(len(problem.IS)) }
                tuning_parameter_store = { problem.PS[k].name:tuning_parameter_orig_list[k] for k in range(len(problem.PS)) }
                constants_store = problem.constants
                if constants_store == None:
                    constants_store = {}
                machine_configuration_store = self.machine_configuration
                software_configuration_store = self.software_configuration
                evaluation_result_store = { problem.OS[k].name:None if np.isnan(evaluation_result_orig_list[k]) else evaluation_result_orig_list[k] for k in range(len(problem.OS)) }

                if "machine_configuration" in task_parameter_store:
                    import ast
                    machine_configuration_store = ast.literal_eval(task_parameter_store["machine_configuration"])
                    del task_parameter_store["machine_configuration"]
                if "software_configuration" in task_parameter_store:
                    import ast
                    software_configuration_store = ast.literal_eval(task_parameter_store["software_configuration"])
                    del task_parameter_store["software_configuration"]

                new_function_evaluation_results.append({
                        "task_parameter":task_parameter_store,
                        "tuning_parameter":tuning_parameter_store,
                        "constants":constants_store,
                        "machine_configuration":machine_configuration_store,
                        "software_configuration":software_configuration_store,
                        "evaluation_result":evaluation_result_store,
                        "source": source,
                        "time":{
                            "tm_year":now.tm_year,
                            "tm_mon":now.tm_mon,
                            "tm_mday":now.tm_mday,
                            "tm_hour":now.tm_hour,
                            "tm_min":now.tm_min,
                            "tm_sec":now.tm_sec,
                            "tm_wday":now.tm_wday,
                            "tm_yday":now.tm_yday,
                            "tm_isdst":now.tm_isdst
                            },
                        "uid":str(uid)
                    })

            if self.file_synchronization_method == 'filelock':
                with FileLock(json_data_path+".lock"):
                    with open(json_data_path, "r") as f_in:
                        json_data = json.load(f_in)
                        json_data["func_eval"] += new_function_evaluation_results
                    with open(json_data_path, "w") as f_out:
                        json.dump(json_data, f_out, indent=2)
            elif self.file_synchronization_method == 'rsync':
                while True:
                    temp_path = json_data_path + "." + self.process_uid + ".temp"
                    os.system("rsync -a " + json_data_path + " " + temp_path)
                    with open(temp_path, "r") as f_in:
                        json_data = json.load(f_in)
                        json_data["func_eval"] += new_function_evaluation_results
                    with open(temp_path, "w") as f_out:
                        json.dump(json_data, f_out, indent=2)
                    os.system("rsync -u " + temp_path + " " + json_data_path)
                    os.system("rm " + temp_path)
                    with open(json_data_path, "r") as f_in:
                        json_data = json.load(f_in)
                        existing_uids = [item["uid"] for item in json_data["func_eval"]]
                        new_uids = [item["uid"] for item in new_function_evaluation_results]
                        retry = False
                        for uid in new_uids:
                            if uid not in existing_uids:
                                retry = True
                                break
                        if retry == False:
                            break
            else:
                with open(json_data_path, "r") as f_in:
                    json_data = json.load(f_in)
                    json_data["func_eval"] += new_function_evaluation_results
                with open(json_data_path, "w") as f_out:
                    json.dump(json_data, f_out, indent=2)

        return

    def check_surrogate_model_exact_match(self,
            surrogate_model : dict,
            task_parameters_given: np.array,
            input_space_given: list,
            parameter_space_given: list,
            output_space_given: list):

        model_task_parameters = surrogate_model["task_parameters"]
        if len(model_task_parameters) != len(task_parameters_given):
            return False
        num_tasks = len(task_parameters_given)
        for i in range(num_tasks):
            if len(model_task_parameters[i]) != len(task_parameters_given[i]):
                return False
            for j in range(len(task_parameters_given[i])):
                if model_task_parameters[i][j] != task_parameters_given[i][j]:
                    return False

        for space_model in surrogate_model["input_space"]:
            space_given = next((item for item in input_space_given if item["name"] == space_model["name"]), None)
            if space_given == None:
                return False
            if space_model["type"] != space_given["type"]:
                return False
            if space_model["transformer"] != space_given["transformer"]:
                return False
            if space_model["lower_bound"] != space_given["lower_bound"]:
                return False
            if space_model["upper_bound"] != space_given["upper_bound"]:
                return False

        for space_model in surrogate_model["parameter_space"]:
            space_given = next((item for item in parameter_space_given if item["name"] == space_model["name"]), None)
            if space_given == None:
                return False
            if space_model["type"] != space_given["type"]:
                return False
            if space_model["transformer"] != space_given["transformer"]:
                return False
            if space_model["lower_bound"] != space_given["lower_bound"]:
                return False
            if space_model["upper_bound"] != space_given["upper_bound"]:
                return False

        for space_model in surrogate_model["output_space"]:
            space_given = next((item for item in output_space_given if item["name"] == space_model["name"]), None)
            if space_given == None:
                return False
            if space_model["type"] != space_given["type"]:
                return False
            if space_model["transformer"] != space_given["transformer"]:
                return False
            if space_model["lower_bound"] != space_given["lower_bound"]:
                return False
            if space_model["upper_bound"] != space_given["upper_bound"]:
                return False

        return True

    def check_surrogate_model_usable(self,
            surrogate_model : dict,
            task_parameters_given: np.array,
            input_space_given: list,
            parameter_space_given: list,
            output_space_given: list):

        #print ("check_surrogate_model_usable")
        #print ("surrogate_model: ", surrogate_model)
        #print ("task_parameters_given: ", task_parameters_given)
        #print ("input_space_given: ", input_space_given)
        #print ("parameter_space_given: ", parameter_space_given)
        #print ("output_space_given: ", output_space_given)

        model_task_parameters = surrogate_model["task_parameters"]
        task_parameter_names_given = [item["name"] for item in input_space_given]
        task_parameter_names_model = [item["name"] for item in surrogate_model["input_space"]]
        for input_task in task_parameters_given:
            input_task_ordered = [
                    input_task[task_parameter_names_given.index(name)]
                    for name in task_parameter_names_model]
            if not input_task_ordered in model_task_parameters:
                print ("[HistoryDB] Task information is not found")
                return False

        for space_model in surrogate_model["input_space"]:
            space_given = next((item for item in input_space_given if item["name"] == space_model["name"]), None)
            if space_given == None:
                return False
            if space_model["type"] != space_given["type"]:
                return False
            if space_model["transformer"] != space_given["transformer"]:
                return False
            #if space_model["lower_bound"] != space_given["lower_bound"]:
            #    return False
            #if space_model["upper_bound"] != space_given["upper_bound"]:
            #    return False

        for space_model in surrogate_model["parameter_space"]:
            space_given = next((item for item in parameter_space_given if item["name"] == space_model["name"]), None)
            if space_given == None:
                return False
            if space_model["type"] != space_given["type"]:
                return False
            if space_model["transformer"] != space_given["transformer"]:
                return False
            #if space_model["lower_bound"] != space_given["lower_bound"]:
            #    return False
            #if space_model["upper_bound"] != space_given["upper_bound"]:
            #    return False

        for space_model in surrogate_model["output_space"]:
            space_given = next((item for item in output_space_given if item["name"] == space_model["name"]), None)
            if space_given == None:
                return False
            if space_model["type"] != space_given["type"]:
                return False
            if space_model["transformer"] != space_given["transformer"]:
                return False
            #if space_model["lower_bound"] != space_given["lower_bound"]:
            #    return False
            #if space_model["upper_bound"] != space_given["upper_bound"]:
            #    return False

        return True

    def read_surrogate_models(self, tuningproblem=None, Igiven=None, modeler="Model_LCM"):
        ret = []
        print ("problem ", tuningproblem)
        print ("problem input_space ", self.problem_space_to_dict(tuningproblem.input_space))

        if tuningproblem == "None" or Igiven == "None":
            return ret

        if (self.tuning_problem_name is not None):
            json_data_path = self.history_db_path+"/"+self.tuning_problem_name+".json"
            if os.path.exists(json_data_path):
                if self.file_synchronization_method == 'filelock':
                    with FileLock(json_data_path+".lock"):
                        with open(json_data_path, "r") as f_in:
                            history_data = json.load(f_in)
                elif self.file_synchronization_method == 'rsync':
                    temp_path = json_data_path + "." + self.process_uid + ".temp"
                    os.system("rsync -a " + json_data_path + " " + temp_path)
                    with open(temp_path, "r") as f_in:
                        history_data = json.load(f_in)
                    os.system("rm " + temp_path)
                else:
                    with open(json_data_path, "r") as f_in:
                        history_data = json.load(f_in)

                num_models = len(history_data["surrogate_model"])

                max_evals = 0
                max_evals_index = -1 # TODO: if no model is found?
                for i in range(num_models):
                    surrogate_model = history_data["surrogate_model"][i]
                    if (self.check_surrogate_model_exact_match(
                        surrogate_model,
                        Igiven,
                        self.problem_space_to_dict(tuningproblem.input_space),
                        self.problem_space_to_dict(tuningproblem.parameter_space),
                        self.problem_space_to_dict(tuningproblem.output_space)) and
                        surrogate_model["modeler"] == modeler):
                        ret.append(surrogate_model)

        return ret

    def load_MLE_surrogate_model_hyperparameters(self, tuningproblem : TuningProblem,
            input_given : np.ndarray, objective : int, modeler : str):
        if (self.tuning_problem_name is not None):
            json_data_path = self.history_db_path+"/"+self.tuning_problem_name+".json"
            if os.path.exists(json_data_path):
                if self.file_synchronization_method == 'filelock':
                    with FileLock(json_data_path+".lock"):
                        with open(json_data_path, "r") as f_in:
                            history_data = json.load(f_in)
                elif self.file_synchronization_method == 'rsync':
                    temp_path = json_data_path + "." + self.process_uid + ".temp"
                    os.system("rsync -a " + json_data_path + " " + temp_path)
                    with open(temp_path, "r") as f_in:
                        history_data = json.load(f_in)
                    os.system("rm " + temp_path)
                else:
                    with open(json_data_path, "r") as f_in:
                        history_data = json.load(f_in)

                max_mle = -9999
                max_mle_index = -1
                for i in range(len(history_data["surrogate_model"])):
                    surrogate_model = history_data["surrogate_model"][i]
                    if (self.check_surrogate_model_exact_match(
                        surrogate_model,
                        input_given,
                        self.problem_space_to_dict(tuningproblem.input_space),
                        self.problem_space_to_dict(tuningproblem.parameter_space),
                        self.problem_space_to_dict(tuningproblem.output_space)) and
                        surrogate_model["modeler"] == modeler and
                        surrogate_model["objective_id"] == objective):
                        log_likelihood = surrogate_model["log_likelihood"]
                        if log_likelihood > max_mle:
                            max_mle = log_likelihood
                            max_mle_index = i
                if (max_mle_index == -1):
                    print ("Unable to find a model")
                    return None

                hyperparameters =\
                        history_data["surrogate_model"][max_mle_index]["hyperparameters"]

                parameter_names = []
                for parameter_info in history_db["surrogate_model"][max_mle_index]["parameter_space"]:
                    parameter_names.append(parameter_info["name"])

        return (hyperparameters, parameter_names)

    def load_AIC_surrogate_model_hyperparameters(self, tuningproblem : TuningProblem,
            input_given : np.ndarray, objective : int, modeler : str):
        if (self.tuning_problem_name is not None):
            json_data_path = self.history_db_path+"/"+self.tuning_problem_name+".json"
            if os.path.exists(json_data_path):
                if self.file_synchronization_method == 'filelock':
                    with FileLock(json_data_path+".lock"):
                        with open(json_data_path, "r") as f_in:
                            history_data = json.load(f_in)
                elif self.file_synchronization_method == 'rsync':
                    temp_path = json_data_path + "." + self.process_uid + ".temp"
                    os.system("rsync -a " + json_data_path + " " + temp_path)
                    with open(temp_path, "r") as f_in:
                        history_data = json.load(f_in)
                    os.system("rm " + temp_path)
                else:
                    with open(json_data_path, "r") as f_in:
                        history_data = json.load(f_in)

                min_aic = 99999
                min_aic_index = -1
                for i in range(len(history_data["surrogate_model"])):
                    surrogate_model = history_data["surrogate_model"][i]
                    if (self.check_surrogate_model_exact_match(
                        surrogate_model,
                        input_given,
                        self.problem_space_to_dict(tuningproblem.input_space),
                        self.problem_space_to_dict(tuningproblem.parameter_space),
                        self.problem_space_to_dict(tuningproblem.output_space)) and
                        surrogate_model["modeler"] == modeler and
                        surrogate_model["objective_id"] == objective):
                        log_likelihood = surrogate_model["log_likelihood"]
                        num_parameters = len(surrogate_model["hyperparameters"])
                        AIC = -1.0 * 2.0 * log_likelihood + 2.0 * num_parameters
                        if AIC < min_aic:
                            min_aic = AIC
                            min_aic_index = i
                if (min_aic_index == -1):
                    print ("Unable to find a model")
                    return None

                hyperparameters =\
                        history_data["surrogate_model"][min_aic_index]["hyperparameters"]

                parameter_names = []
                for parameter_info in history_db["surrogate_model"][min_aic_index]["parameter_space"]:
                    parameter_names.append(parameter_info["name"])

        return (hyperparameters, parameter_names)

    def load_BIC_surrogate_model_hyperparameters(self, tuningproblem : TuningProblem,
            input_given : np.ndarray, objective : int, modeler : str):
        import math

        if (self.tuning_problem_name is not None):
            json_data_path = self.history_db_path+"/"+self.tuning_problem_name+".json"
            if os.path.exists(json_data_path):
                if self.file_synchronization_method == 'filelock':
                    with FileLock(json_data_path+".lock"):
                        with open(json_data_path, "r") as f_in:
                            history_data = json.load(f_in)
                elif self.file_synchronization_method == 'rsync':
                    temp_path = json_data_path + "." + self.process_uid + ".temp"
                    os.system("rsync -a " + json_data_path + " " + temp_path)
                    with open(temp_path, "r") as f_in:
                        history_data = json.load(f_in)
                    os.system("rm " + temp_path)
                else:
                    with open(json_data_path, "r") as f_in:
                        history_data = json.load(f_in)

                min_bic = 99999
                min_bic_index = -1
                for i in range(len(history_data["surrogate_model"])):
                    surrogate_model = history_data["surrogate_model"][i]
                    if (self.check_surrogate_model_exact_match(
                        surrogate_model,
                        input_given,
                        self.problem_space_to_dict(tuningproblem.input_space),
                        self.problem_space_to_dict(tuningproblem.parameter_space),
                        self.problem_space_to_dict(tuningproblem.output_space)) and
                        surrogate_model["modeler"] == modeler and
                        surrogate_model["objective_id"] == objective):
                        log_likelihood = surrogate_model["log_likelihood"]
                        num_parameters = len(surrogate_model["hyperparameters"])
                        num_samples = len(surrogate_model["function_evaluations"])
                        BIC = -1.0 * 2.0 * log_likelihood + num_parameters * math.log(num_samples)
                        if BIC < min_bic:
                            min_bic = BIC
                            min_bic_index = i
                if (min_bic_index == -1):
                    print ("Unable to find a model")
                    return None

                hyperparameters =\
                        history_data["surrogate_model"][min_bic_index]["hyperparameters"]

                parameter_names = []
                for parameter_info in history_db["surrogate_model"][min_bic_index]["parameter_space"]:
                    parameter_names.append(parameter_info["name"])

        return (hyperparameters, parameter_names)

    def load_max_evals_surrogate_model_hyperparameters(self, tuningproblem : TuningProblem,
            input_given : np.ndarray, objective : int, modeler : str):
        if (self.tuning_problem_name is not None):
            json_data_path = self.history_db_path+"/"+self.tuning_problem_name+".json"
            if os.path.exists(json_data_path):
                if self.file_synchronization_method == 'filelock':
                    with FileLock(json_data_path+".lock"):
                        with open(json_data_path, "r") as f_in:
                            history_data = json.load(f_in)
                elif self.file_synchronization_method == 'rsync':
                    temp_path = json_data_path + "." + self.process_uid + ".temp"
                    os.system("rsync -a " + json_data_path + " " + temp_path)
                    with open(temp_path, "r") as f_in:
                        history_data = json.load(f_in)
                    os.system("rm " + temp_path)
                else:
                    with open(json_data_path, "r") as f_in:
                        history_data = json.load(f_in)

                max_evals = 0
                max_evals_index = -1 # TODO: if no model is found?
                for i in range(len(history_data["surrogate_model"])):
                    surrogate_model = history_data["surrogate_model"][i]
                    if (self.check_surrogate_model_exact_match(
                        surrogate_model,
                        input_given,
                        self.problem_space_to_dict(tuningproblem.input_space),
                        self.problem_space_to_dict(tuningproblem.parameter_space),
                        self.problem_space_to_dict(tuningproblem.output_space)) and
                        surrogate_model["modeler"] == modeler and
                        surrogate_model["objective_id"] == objective):
                        num_evals = len(history_data["surrogate_model"][i]["function_evaluations"])
                        if num_evals > max_evals:
                            max_evals = num_evals
                            max_evals_index = i
                if (max_evals_index == -1):
                    print ("Unable to find a model")
                    return None

                hyperparameters =\
                        history_data["surrogate_model"][max_evals_index]["hyperparameters"]

                parameter_names = []
                for parameter_info in history_data["surrogate_model"][max_evals_index]["parameter_space"]:
                    parameter_names.append(parameter_info["name"])

        return (hyperparameters, parameter_names)

    def load_surrogate_model_hyperparameters_by_uid(self, model_uid):
        if (self.tuning_problem_name is not None):
            json_data_path = self.history_db_path+"/"+self.tuning_problem_name+".json"
            if os.path.exists(json_data_path):
                if self.file_synchronization_method == 'filelock':
                    with FileLock(json_data_path+".lock"):
                        with open(json_data_path, "r") as f_in:
                            history_data = json.load(f_in)
                elif self.file_synchronization_method == 'rsync':
                    temp_path = json_data_path + "." + self.process_uid + ".temp"
                    os.system("rsync -a " + json_data_path + " " + temp_path)
                    with open(temp_path, "r") as f_in:
                        history_data = json.load(f_in)
                    os.system("rm " + temp_path)
                else:
                    with open(json_data_path, "r") as f_in:
                        history_data = json.load(f_in)

                surrogate_model = history_data["surrogate_model"]
                num_models = len(surrogate_model)
                for i in range(num_models):
                    if surrogate_model[i]["uid"] == model_uid:
                        return surrogate_model[i]["hyperparameters"]

        return []

    def load_surrogate_model_meta_data(self,
            task_parameters_given: np.ndarray,
            tuning_configuration: dict,
            input_space_given: dict,
            parameter_space_given: dict,
            output_space_given: dict,
            objective: int,
            modeler: str):
            #tuningproblem : TuningProblem,
            #input_given : np.ndarray, objective : int, modeler : str):
        if (self.tuning_problem_name is not None):
            json_data_path = self.history_db_path+"/"+self.tuning_problem_name+".json"
            if os.path.exists(json_data_path):
                if self.file_synchronization_method == 'filelock':
                    with FileLock(json_data_path+".lock"):
                        with open(json_data_path, "r") as f_in:
                            history_data = json.load(f_in)
                elif self.file_synchronization_method == 'rsync':
                    temp_path = json_data_path + "." + self.process_uid + ".temp"
                    os.system("rsync -a " + json_data_path + " " + temp_path)
                    with open(temp_path, "r") as f_in:
                        history_data = json.load(f_in)
                    os.system("rm " + temp_path)
                else:
                    with open(json_data_path, "r") as f_in:
                        history_data = json.load(f_in)

                max_evals = 0
                max_evals_index = -1 # TODO: if no model is found?
                for i in range(len(history_data["surrogate_model"])):
                    surrogate_model = history_data["surrogate_model"][i]
                    if (self.check_surrogate_model_usable(surrogate_model,
                        task_parameters_given,
                        input_space_given,
                        parameter_space_given,
                        output_space_given) and
                        surrogate_model["modeler"] == modeler and
                        surrogate_model["objective_id"] == objective):

                        tuning_configuration_match = True
                        for func_eval_uid in surrogate_model["function_evaluations"]:
                            func_eval = search_item_by_uid(history_data["func_eval"], func_eval_uid)
                            #print ("tuning_configuration (machine): ", tuning_configuration["machine_configuration"])
                            #print ("func_eval (machine):            ", func_eval["machine_configuration"])
                            if tuning_configuration != None:
                                if str(tuning_configuration["machine_configuration"]) != str(func_eval["machine_configuration"]):
                                    #print ("not same")
                                    tuning_configuration_match = False
                                    break
                                #else:
                                #    print ("same")

                            #if tuning_configuration != None and tuning_configuration["software_configuration"] != func_eval["software_configuration"]:
                            #    tuning_configuration_match = False
                            #    break
                        if tuning_configuration_match:
                            num_evals = len(history_data["surrogate_model"][i]["function_evaluations"])
                            if num_evals > max_evals:
                                max_evals = num_evals
                                max_evals_index = i
                if (max_evals_index == -1):
                    print ("Unable to find a surrogate model")
                    return None

        return history_data["surrogate_model"][max_evals_index]

    def load_surrogate_model_configurations(self,
            task_parameters_given: np.ndarray,
            input_space_given: dict,
            parameter_space_given: dict,
            output_space_given: dict,
            loadable_machine_configurations: dict,
            loadable_software_configurations: dict,
            objective: int,
            modeler: str):

        model_configurations = []

        if (self.tuning_problem_name is not None):
            json_data_path = self.history_db_path+"/"+self.tuning_problem_name+".json"
            if os.path.exists(json_data_path):
                if self.file_synchronization_method == 'filelock':
                    with FileLock(json_data_path+".lock"):
                        with open(json_data_path, "r") as f_in:
                            history_data = json.load(f_in)
                elif self.file_synchronization_method == 'rsync':
                    temp_path = json_data_path + "." + self.process_uid + ".temp"
                    os.system("rsync -a " + json_data_path + " " + temp_path)
                    with open(temp_path, "r") as f_in:
                        history_data = json.load(f_in)
                    os.system("rm " + temp_path)
                else:
                    with open(json_data_path, "r") as f_in:
                        history_data = json.load(f_in)

                for surrogate_model in history_data["surrogate_model"]:

                    if (self.check_surrogate_model_usable(surrogate_model,
                        task_parameters_given,
                        input_space_given,
                        parameter_space_given,
                        output_space_given) and
                        surrogate_model["modeler"] == modeler and
                        surrogate_model["objective_id"] == objective):
                        #print (surrogate_model)

                        for func_eval_uid in surrogate_model["function_evaluations"]:
                            func_eval = search_item_by_uid(history_data["func_eval"], func_eval_uid)

                            configuration = {
                                    "task_parameters": surrogate_model["task_parameters"],
                                    "machine_configuration": func_eval["machine_configuration"],
                                    "software_configuration": func_eval["software_configuration"]
                                    }

                            if configuration not in model_configurations:
                                model_configurations.append(configuration)

        return (model_configurations)

    def problem_space_to_dict(self, space : Space):

        dict_arr = []

        space_len = len(space)

        transformers = space.get_transformer()

        for i in range(space_len):
            dict_ = {}

            dict_["name"] = space[i].name

            dict_["transformer"] = transformers[i]

            space_type_name = type(space[i]).__name__

            if space_type_name == "Real":
                dict_["type"] = "real"

                lower_bound, upper_bound = space.bounds[i]
                dict_["lower_bound"] = lower_bound
                dict_["upper_bound"] = upper_bound

            elif space_type_name == "Integer":
                dict_["type"] = "int"

                lower_bound, upper_bound = space.bounds[i]
                dict_["lower_bound"] = lower_bound
                dict_["upper_bound"] = upper_bound

            elif space_type_name == "Categoricalnorm":
                dict_["type"] = "categorical"
                dict_["categories"] = space[i].bounds

            else:
                print ("space type unknown")

            dict_arr.append(dict_)

        return dict_arr

    def store_model_LCM(self,\
            objective : int,
            problem : Problem,\
            input_given : np.ndarray,\
            bestxopt : np.ndarray,\
            neg_log_marginal_likelihood : float,\
            gradients : np.ndarray,\
            iteration : int):

        if (self.tuning_problem_name is not None):
            json_data_path = self.history_db_path+"/"+self.tuning_problem_name+".json"

            new_surrogate_models = []

            now = time.localtime()

            #from scipy.stats.mstats import gmean
            #from scipy.stats.mstats import hmean
            model_stats = {}
            model_stats["log_likelihood"] = -1.0 * neg_log_marginal_likelihood
            model_stats["neg_log_likelihood"] = neg_log_marginal_likelihood
            model_stats["gradients"] = gradients.tolist()
            #model_stats["gradients_sum_abs"] = np.sum(np.absolute(gradients))
            #model_stats["gradients_average_abs"] = np.average(np.absolute(gradients))
            #model_stats["gradients_hmean_abs"] = hmean(np.absolute(gradients))
            #model_stats["gradients_gmean_abs"] = gmean(np.absolute(gradients))
            model_stats["iterations"] = iteration

            gradients_list = gradients.tolist()

            #problem_space = {}
            #problem_space["input_space"] = self.problem_space_to_dict(problem.IS)
            #problem_space["parameter_space"] = self.problem_space_to_dict(problem.PS)
            #problem_space["output_space"] = self.problem_space_to_dict(problem.OS)

            task_parameter_orig = problem.IS.inverse_transform(np.array(input_given, ndmin=2))
            task_parameter_orig_list = np.array(task_parameter_orig).tolist()
            #task_parameter_dict_list = []
            #for i in range(len(input_given)):
            #    task_parameter_dict = {problem.IS[k].name:task_parameter_orig_list[i][k] for k in range(len(problem.IS))}
            #    task_parameter_dict_list.append(task_parameter_dict)

            new_surrogate_models.append({
                    "hyperparameters":bestxopt.tolist(),
                    "model_stats":model_stats,
                    "task_parameters":task_parameter_orig_list,
                    "function_evaluations":self.uids,
                    "input_space":self.problem_space_to_dict(problem.IS),
                    "parameter_space":self.problem_space_to_dict(problem.PS),
                    "output_space":self.problem_space_to_dict(problem.OS),
                    "modeler":"Model_LCM",
                    "objective_id":objective,
                    "time":{
                        "tm_year":now.tm_year,
                        "tm_mon":now.tm_mon,
                        "tm_mday":now.tm_mday,
                        "tm_hour":now.tm_hour,
                        "tm_min":now.tm_min,
                        "tm_sec":now.tm_sec,
                        "tm_wday":now.tm_wday,
                        "tm_yday":now.tm_yday,
                        "tm_isdst":now.tm_isdst
                        },
                    "uid":str(uuid.uuid1())
                    # objective id is to dinstinguish between different models for multi-objective optimization;
                    # we might need a nicer way to manage different models
                })

            if self.file_synchronization_method == 'filelock':
                with FileLock(json_data_path+".lock"):
                    with open(json_data_path, "r") as f_in:
                        json_data = json.load(f_in)
                        json_data["surrogate_model"] += new_surrogate_models
                    with open(json_data_path, "w") as f_out:
                        json.dump(json_data, f_out, indent=2)
            elif self.file_synchronization_method == 'rsync':
                while True:
                    temp_path = json_data_path + "." + self.process_uid + ".temp"
                    os.system("rsync -a " + json_data_path + " " + temp_path)
                    with open(temp_path, "r") as f_in:
                        json_data = json.load(f_in)
                        json_data["surrogate_model"] += new_surrogate_models
                    with open(temp_path, "w") as f_out:
                        json.dump(json_data, f_out, indent=2)
                    os.system("rsync -u " + temp_path + " " + json_data_path)
                    os.system("rm " + temp_path)
                    with open(json_data_path, "r") as f_in:
                        json_data = json.load(f_in)
                        existing_uids = [item["uid"] for item in json_data["surrogate_model"]]
                        new_uids = [item["uid"] for item in new_surrogate_models]
                        retry = False
                        for uid in new_uids:
                            if uid not in existing_uids:
                                retry = True
                                break
                        if retry == False:
                            break
            else:
                with open(json_data_path, "r") as f_in:
                    json_data = json.load(f_in)
                    json_data["surrogate_model"] += new_surrogate_models
                with open(json_data_path, "w") as f_out:
                    json.dump(json_data, f_out, indent=2)

        return