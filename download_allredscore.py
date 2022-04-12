# -*- coding: utf-8 -*-

# * Copyright (c) 2009-2018. Authors: see NOTICE file.
# *
# * Licensed under the Apache License, Version 2.0 (the "License");
# * you may not use this file except in compliance with the License.
# * You may obtain a copy of the License at
# *
# *      http://www.apache.org/licenses/LICENSE-2.0
# *
# * Unless required by applicable law or agreed to in writing, software
# * distributed under the License is distributed on an "AS IS" BASIS,
# * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# * See the License for the specific language governing permissions and
# * limitations under the License.

# from __future__ import print_function, unicode_literals, absolute_import, division


##==== inside a folder containing Dockerfile, run: sudo docker build -t cytomine/s_python_classifypncell ====##

import sys
import numpy as np
import os
import cytomine
from glob import glob

from cytomine import Cytomine, models, CytomineJob
from cytomine.models import Annotation, AnnotationTerm, AnnotationCollection, ImageInstanceCollection, Job, JobData, Project, ImageInstance, Property
from cytomine.models.ontology import Ontology, OntologyCollection, Term, RelationTerm, TermCollection

import time
import re

from argparse import ArgumentParser
import json
import logging
import shutil



__author__ = "WSH Munirah W Ahmad <wshmunirah@gmail.com>"
__copyright__ = "Apache 2 license. Made by Multimedia University Cytomine Team, Cyberjaya, Malaysia, http://cytomine.mmu.edu.my/"
__version__ = "1.0.4"
# Date created : 07 April 2022

def run(cyto_job, parameters):
    logging.info("----- Download Allred Score v%s -----", __version__)
    logging.info("Entering run(cyto_job=%s, parameters=%s)", cyto_job, parameters)

    job = cyto_job.job
    user = job.userJob
    project = cyto_job.project

    terms = TermCollection().fetch_with_filter("project", project.id)
    # conn.job.update(status=Job.RUNNING, progress=1, statusComment="Terms collected...")
    print(terms)

    start_time=time.time()

       
    #Select images to process
    images = ImageInstanceCollection().fetch_with_filter("project", project.id)
    # conn.job.update(status=Job.RUNNING, progress=2, statusComment="Images gathered...")
    
    # print('images id:',images)

    list_imgs = []
    if parameters.cytomine_id_images == 'all':
        for image in images:
            list_imgs.append(int(image.id))
    else:
        # list_imgs = [int(id_img) for id_img in parameters.cytomine_id_images.split(',')]
        list_imgs = parameters.cytomine_id_images
        list_imgs2 = list_imgs.split(',')
    
    print('Input param:', parameters.cytomine_id_images)
    print('Print list images:', list_imgs)
    print(type(list_imgs))
    # list_imgs2 = list_imgs.split(',')
    print(type(list_imgs2))
    print('Print list images2:', list_imgs2)
    # for id_image in list_imgs2:
    #     print(id_image) 

    working_path = os.path.join("tmp",str(job.id))

    if not os.path.exists(working_path):
        logging.info("Creating working directory: %s", working_path)
        os.makedirs(working_path)

    try:
        output_path = os.path.join(working_path, "WSI_scoring_results.csv")
        f= open(output_path,"w+")
        f.write("Image ID;Class Prediction;Class 0 (Negative);Class 1 (Weak);Class 2 (Moderate);Class 3 (Strong);Total Prediction;Total Positive;Class Positive Max;Positive Percentage;Proportion Score;Intensity Score;Allred Score;Execution Time;Prediction Time \n")
            

        #Go over images
        for id_image in list_imgs2:
            print('Current image:', id_image)
            roi_annotations = AnnotationCollection()
            roi_annotations.project = project.id
            # roi_annotations.term = parameters.id_cell_term
            roi_annotations.image = id_image #conn.parameters.cytomine_id_image            
            # roi_annotations.showWKT = True
            roi_annotations.showTerm = True

            if parameters.cytomine_id_user_job != 0:
                roi_annotations.job = parameters.cytomine_id_annotation_job
                roi_annotations.user = parameters.cytomine_id_user_job

            roi_annotations.fetch()
            # print(roi_annotations)

            current_im = ImageInstance().fetch(id_image)
            # current_im2 = 

            start_scoring_time=time.time()
            # predictions = []
            # img_all = []
            pred_all = []
            pred_c0 = 0
            pred_c1 = 0
            pred_c2 = 0
            pred_c3 = 0


            for i, roi in enumerate(roi_annotations):
                term=roi.term
                # term=int(term)
                # regex = '\d+'          
                # term = re.findall(regex, term)
                # print(term)
                

                if term==[parameters.cytomine_id_c0_term]:
                    pred_c0=pred_c0+1                
                elif term==[parameters.cytomine_id_c1_term]:
                    pred_c1=pred_c1+1
                elif term==[parameters.cytomine_id_c2_term]:
                    pred_c2=pred_c2+1
                elif term==[parameters.cytomine_id_c3_term]:
                    pred_c3=pred_c3+1


            pred_all=[pred_c0, pred_c1, pred_c2, pred_c3]
            pred_positive_all=[pred_c1, pred_c2, pred_c3]
            print("pred_all:", pred_all)
            im_pred = np.argmax(pred_all)
            print("image prediction:", im_pred)
            pred_total=pred_c0+pred_c1+pred_c2+pred_c3
            print("pred_total:",pred_total)
            pred_positive=pred_c1+pred_c2+pred_c3
            print("pred_positive:",pred_positive)
            print("pred_positive_all:",pred_positive_all)
            print("pred_positive_max:",np.argmax(pred_positive_all))
            pred_positive_100=pred_positive/pred_total*100
            print("pred_positive_100:",pred_positive_100)

            if pred_positive_100 == 0:
                proportion_score = 0
            elif pred_positive_100 < 1:
                proportion_score = 1
            elif pred_positive_100 >= 1 and pred_positive_100 <= 10:
                proportion_score = 2
            elif pred_positive_100 > 10 and pred_positive_100 <= 33:
                proportion_score = 3
            elif pred_positive_100 > 33 and pred_positive_100 <= 66:
                proportion_score = 4
            elif pred_positive_100 > 66:
                proportion_score = 5

            if pred_positive_100 == 0:
                intensity_score = 0
            elif im_pred == 0:
                intensity_score = np.argmax(pred_positive_all)+1
            elif im_pred == 1:
                intensity_score = 1
            elif im_pred == 2:
                intensity_score = 2
            elif im_pred == 3:
                intensity_score = 3

            allred_score = proportion_score + intensity_score
            print('Proportion Score: ',proportion_score)
            print('Intensity Score: ',intensity_score)            
            print('Allred Score: ',allred_score)
            # shutil.rmtree(roi_path, ignore_errors=True)
            
            end_time=time.time()
            print("Execution time: ",end_time-start_time)
            print("Scoring time: ",end_time-start_scoring_time)
            
            
            f.write("{};{};{};{};{};{};{};{};{};{};{};{};{};{};{}\n".format(id_image,im_pred,pred_c0,pred_c1,pred_c2,pred_c3,pred_total,pred_positive,np.argmax(pred_positive_all),pred_positive_100,proportion_score,intensity_score,allred_score,end_time-start_time,end_time-start_scoring_time))
            # f.write(" \n")
        f.close()
        job_data = JobData(job.id, "Generated File", "WSI_scoring_results.csv").save()
        job_data.upload(output_path)

    finally:
        logging.info("Deleting folder %s", working_path)
        shutil.rmtree(working_path, ignore_errors=True)
        logging.debug("Leaving run()")

    job.update(status=Job.TERMINATED, progress=100, statusComment="Finished.") 


if __name__ == "__main__":
    logging.debug("Command: %s", sys.argv)

    with cytomine.CytomineJob.from_cli(sys.argv) as cyto_job:
        run(cyto_job, cyto_job.parameters)




