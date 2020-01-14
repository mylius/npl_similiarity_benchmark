import numpy as np
from scipy.stats import pearsonr
from scipy.stats import spearmanr
from sklearn.metrics import mean_squared_error
from sklearn import preprocessing
import argparse
import algs
import util
import time
import json
from collections import OrderedDict


class Dataset_annot():
    """
    A class that stores a dataset of annotated semantic similarity data and allows the benchmarking of algorithms on it.
    There are loading functions for the SICK and the STS dataset predefinded [load_sts(),load_sick()].
    The compare() function will return the difference between a given algorithm's results and the groundtruth according to a given metric. 

    Parameters
    ----------
    name : A name for the dataset.


    Example
    ----------
    db = Dataset_annot("sick")
    db.load_sick()
    alg = algs.BagOfWords()
    alg.train(db.train_data)
    db.compare(pearsonr, alg)
    """
    def __init__(self, name):
        self.name = name
        self.train_data = [[], []]
        self.test_data = [[], []]
        self.train_score = []
        self.test_score = []
        self.train_ids = []
        self.test_ids = []
        self.results = {}
        self.phrase_vecs = {}
        self.sick = False
        self.sts = False

    def load(self, path, data_cols, data, score_col, scores, id_col=None, ids=None):
        """
        Loads data into the dataset_annot class.

        Parameters
        ----------
        path : path to the file containing the data.
        data_cols : Indizes of the columns containing the sentences as a list.
        data : The data field in Dataset_annot() that should be filled.
        score_col : Index of the column in the file containing the scores.
        scores :  The score field in Dataset_annot() that should be filled.
        score_col : Index of the column in the file containing the ids.
        scores :  The id field in Dataset_annot() that should be filled.
        """
        with open(path, "r") as f:
            next(f)
            for line in f.readlines():
                line = line.split("\t")
                for idx, row in enumerate(data_cols):
                    data[idx].append(line[row])
                scores.append(float(line[score_col]))
                if id_col != None:
                    ids.append(line[id_col])

    def load_sick(self):
        """Loads the SICK dataset."""
        self.load("./data/SICK_train.txt", [1, 2],
                  self.train_data, 3, self.train_score, 0, self.train_ids)
        self.load("./data/SICK.txt", [1, 2],
                  self.test_data, 3, self.test_score, 0, self.test_ids)
        self.sick = True

    def load_sts(self):
        """Loads the SICK dataset."""
        self.load("./data/sts_train/raw_gs.txt", [1, 2],
                  self.train_data, 0, self.train_score)
        self.load("./data/sts_test/raw_gs.txt", [1, 2],
                  self.test_data, 0, self.test_score)
        self.sts = True

    def norm_results(self, feature_range):
        """
        Creates lists of normed results.

        Parameters
        ----------
        feature_range : A tuple containing the lowest achievable score and the highest.
        """
        self.normed_results = {}
        for key in self.results:
            if key not in self.normed_results:
                self.normed_results[key] = preprocessing.minmax_scale(
                    self.results[key], feature_range)

    def calc_vecs(self, alg):
        """
        Precalculates the vectors and stores them in memory.
        
        Parameters
        ----------
        alg : The Algorithm to be used to create the sentence vectors."""
        if not alg.trained:
            alg.train(self.train_data)
        self.phrase_vecs[alg] = [[], []]
        print("Creating Vectors")
        for item0, item1 in zip(self.test_data[0], self.test_data[1]):
            self.phrase_vecs[alg][0].append(alg.create_vec(item0))
            self.phrase_vecs[alg][1].append(alg.create_vec(item1))

    def calc_results(self, alg):
        """
        Runs a given algorithm and stores the calculted similarities.
        
        Parameters
        ----------
        alg : The Algorithm to be used to calculate the similarity between two senteces."""
        results = []
        if not alg.trained:
            alg.train(self.train_data)
        if alg in self.phrase_vecs:
            data = self.phrase_vecs[alg]
        else:
            self.calc_vecs(alg)
        for vec1, vec2 in zip(self.phrase_vecs[alg][0], self.phrase_vecs[alg][1]):
            res = float(alg.compare(
                vec1, vec2))
            results.append(res)
        self.results[alg] = results

    def compare(self, function, alg):
        """
        Runs a given algorithm, calculates the difference between groundtruth and the results according to a given metric.
        
        Parameters
        ----------
        alg : The Algorithm to be used to calculate the similarity between the sentece paris.
        function : A function that calculates the metric given two matricies.
        """
        if alg not in self.results:
            self.calc_results(alg)
        if self.sick:
            self.norm_results((1, 5))
        elif self.sts:
            self.norm_results((0, 5))
        return function(self.normed_results[alg], self.test_score)

    def output_sick(self, alg):
        if self.sick:
            with open("./data/results_SICK_{}".format(alg.name), "w+") as data:
                output = "pair_ID \t entailment_judgment \t relatedness_score\n"
                for idx, res in zip(self.test_ids, self.results[alg]):
                    output += "{} \t NA \t {}\n".format(
                        idx, res*4+1)
                data.write(output)


def run_alg(alg, db):
    result = {}
    result["traintime"] = round(util.measure_time(
        "Traintime", alg.train, db.train_data), 3)
    starttime = time.time()
    result["pearson"] = round(db.compare(pearsonr, alg)[0], 3)
    result["spearman"] = round(db.compare(spearmanr, alg)[0], 3)
    result["mre"] = round(db.compare(mean_squared_error, alg), 3)
    endtime = time.time()
    result["runtime"] = round(endtime-starttime, 3)
    result["alg"] = alg.name
    result["db"] = db.name

    return result


def benchmark(algorithms):
    db2 = Dataset_annot("sts")
    db2.load_sts()
    print("Results for STS dataset:")
    run_results = {}
    for alg in algorithms:
        run_results[alg.name +
                    db2.name] = run_alg(alg, db2)
    db = Dataset_annot("sick")
    db.load_sick()
    print("Results for SICK dataset:")
    for alg in algorithms:
        run_results[alg.name + db.name] = run_alg(alg, db)
        # db.output_sick(alg)
    output = []
    for res in run_results:
        output.append(run_results[res])
    with open("./data/results.json", "w+") as f:
        json.dump(output, f, indent=2)


def create_alg_list(in_list):
    """
    Returns a list of algorithms to be run when given a list of commandline arguments as strings.
    
    Parameters
    ----------
    in_list : A list of commandline arguments that identify the algorithms that should be benchmarked.
    """
    alg_list = []
    Algorithms = OrderedDict()
    Algorithms["bow"] = algs.BagOfWords
    Algorithms["bow_j"] = algs.BagOfWords_jaccard
    Algorithms["bow_l2"] = algs.BagOfWords_l2
    Algorithms["bow_s"] = algs.BagOfWords_stop
    Algorithms["bow_l2_s"] = algs.BagOfWords_l2_stop
    Algorithms["bow_j_s"] = algs.BagOfWords_jaccard_stop
    Algorithms["bow_l"] = algs.BagOfWords_lemma
    Algorithms["bow_ls"] = algs.BagOfWords_lemma_stop
    Algorithms["bow_j_l"] = algs.BagOfWords_jaccard_lemma
    Algorithms["bow_j_ls"] = algs.BagOfWords_jaccard_lemma_stop
    Algorithms["bow_l2_l"] = algs.BagOfWords_l2_lemma
    Algorithms["bow_l2_ls"] = algs.BagOfWords_l2_lemma_stop
    Algorithms["spacy_w2v"] = algs.spacy_sem_sim
    Algorithms["spacy_bert"] = algs.spacy_bert
    Algorithms["gensim_wmd"] = algs.gensim_wmd
    if in_list != None:
        in_list = in_list.split(",")
        for alg in in_list:
            if alg in Algorithms:
                alg_list.append(Algorithms[alg]())
    else:
        for alg in Algorithms:
            alg_list.append(Algorithms[alg]())
    return alg_list


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Benchmarks Semantic Similiarty Benchmarks")
    parser.add_argument("algs", metavar="algs", type=str, nargs='?',
                        help="Choose which Algorithms to run by passing arguments: bow - simple bag of words, bow_l - bag of words using lemmatisation, bow_ls - bag of words eliminating stopwords using lemmatisation and",)
    args = parser.parse_args()
    benchmark(create_alg_list(args.algs))
