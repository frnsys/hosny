"""
values sourced from Table 2 of:

    Offering a Job: Meritocracy and Social Networks. Trond Petersen, Ishak Saporta, Marc-David L. Seidel. AJS Volume 106 Number 3 (November 2000): 763-816.
    https://web.stanford.edu/group/scspi/_media/pdf/Reference%20Media/Petersen_Saporta_Seidel_2000_Social%20Networks.pdf

"""
import json


n_applicants = 35229
n_applicants_m = 26376
n_applicants_f = 8853

n_offered = 3432
n_offered_m = 2608
n_offered_f = 824

p_offered = n_offered/n_applicants

p = {
    'sex': {
        'male': n_offered_m/n_applicants_m,     # P(offered|m)
        'female': n_offered_f/n_applicants_f    # P(offered|f)
    },
    'race': {},
    'referral': {}
}

# P(offered|white)
p_r = 0.491
p_r_given_offered = 0.601
p['race']['white'] = (p_offered * p_r_given_offered)/p_r

# P(offered|asian)
p_r = 0.387
p_r_given_offered = 0.313
p['race']['asian'] = (p_offered * p_r_given_offered)/p_r

# P(offered|black)
p_r = 0.072
p_r_given_offered = 0.045
p['race']['black'] = (p_offered * p_r_given_offered)/p_r

# P(offered|hispanic)
p_r = 0.048
p_r_given_offered = 0.041
p['race']['hispanic'] = (p_offered * p_r_given_offered)/p_r

# P(offered|nativeamerican)
p_r = 0.001
p_r_given_offered = 0.001
p['race']['nativeamerican'] = (p_offered * p_r_given_offered)/p_r

# P(offered|friend)
p_r = 0.51
p_r_given_offered = 0.677
p['referral']['friend'] = (p_offered * p_r_given_offered)/p_r

# P(offered|ad or cold call)
p_r = 0.059 + 0.143
p_r_given_offered = 0.014 + 0.061
p['referral']['ad_or_cold_call'] = (p_offered * p_r_given_offered)/p_r

# P(offered|headhunter or campus recruiter)
p_r = 0.035 + 0.148
p_r_given_offered = 0.049 + 0.055
p['referral']['headhunter_or_campus_recruiter'] = (p_offered * p_r_given_offered)/p_r

# P(offered|previous contractor)
p_r = 0.094
p_r_given_offered = 0.132
p['referral']['previous_contractor'] = (p_offered * p_r_given_offered)/p_r

# P(offered|other)
p_r = 0.01
p_r_given_offered = 0.011
p['referral']['other'] = (p_offered * p_r_given_offered)/p_r



p_noffered = 1 - p_offered
n_not_offered = 31797

p_r = n_applicants_m/n_applicants
n_male_not_offered = 23768
n_female_not_offered = 8029
p_r_given_offered = n_male_not_offered/n_not_offered

p_not = {
    'sex': {
        'male': (p_noffered * n_male_not_offered/n_not_offered)/p_r, # P(!offered|male)
        'female': (p_noffered * n_female_not_offered/n_not_offered)/p_r, # P(!offered|female)
    },
    'race': {},
    'referral': {}
}

# P(!offered|white)
p_r = 0.491
p_r_given_noffered = 0.479
p_not['race']['white'] = (p_noffered * p_r_given_noffered)/p_r

# P(!offered|asian)
p_r = 0.387
p_r_given_noffered = 0.395
p_not['race']['asian'] = (p_noffered * p_r_given_noffered)/p_r

# P(!offered|black)
p_r = 0.072
p_r_given_noffered = 0.075
p_not['race']['black'] = (p_noffered * p_r_given_noffered)/p_r

# P(!offered|hispanic)
p_r = 0.048
p_r_given_noffered = 0.049
p_not['race']['hispanic'] = (p_noffered * p_r_given_noffered)/p_r

# P(!offered|nativeamerican)
p_r = 0.001
p_r_given_noffered = 0.001
p_not['race']['nativeamerican'] = (p_noffered * p_r_given_noffered)/p_r

# P(!offered|friend)
p_r = 0.51
p_r_given_noffered = 0.483
p_not['referral']['friend'] = (p_noffered * p_r_given_noffered)/p_r

# P(!offered|ad or cold call)
p_r = 0.059 + 0.143
p_r_given_noffered =  0.064 + 0.171
p_not['referral']['ad_or_cold_call'] = (p_noffered * p_r_given_noffered)/p_r

# P(!offered|headhunter or campus recruiter)
p_r = 0.035 + 0.148
p_r_given_noffered =  0.026 + 0.144
p_not['referral']['headhunter_or_campus_recruiter'] = (p_noffered * p_r_given_noffered)/p_r

# P(!offered|previous contractor)
p_r = 0.094
p_r_given_noffered =  0.102
p_not['referral']['previous_contractor'] = (p_noffered * p_r_given_noffered)/p_r

# P(!offered|other)
p_r = 0.01
p_r_given_noffered =  0.01
p_not['referral']['other'] = (p_noffered * p_r_given_noffered)/p_r

with open('gen/job_offer_probs.json', 'w') as f:
    json.dump({
        'offered': p,
        'not_offered': p_not
    }, f)
