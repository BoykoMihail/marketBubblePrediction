#!/usr/bin/env python

import random
import numpy as np
import pandas as pd
import multiprocessing
from scipy.optimize import minimize
from matplotlib import pyplot as plt


class LPPLS(object):

    def __init__(self, observations):
    
        self.observations = observations
        self.coef_ = {}
        self.indicator_result = []
        
    def fit(self, observations, max_searches, minimizer='Nelder-Mead'):
        search_count = 0
        # find bubble
        while search_count < max_searches:
            tc_init_min, tc_init_max = self._get_tc_bounds(observations, 0.20, 0.20)
            
            init_limits = [
                (tc_init_min, tc_init_max),  # tc
                (0, 2),  # m
                (1, 50),  # ω
            ]

            non_linear_vals = [random.uniform(a[0], a[1]) for a in init_limits]

            tc = non_linear_vals[0]
            m = non_linear_vals[1]
            w = non_linear_vals[2]
            seed = np.array([tc, m, w])

            try:
                tc, m, w, a, b, c, c1, c2 = self.minimize(observations, seed, minimizer)
                return tc, m, w, a, b, c, c1, c2
            except (np.linalg.LinAlgError, UnboundLocalError, ValueError):
                search_count += 1

        return 0, 0, 0, 0, 0, 0, 0, 0
        
    def minimize(self, observations, seed, minimizer):
    
        cofs = minimize(
            args=observations,
            fun=self.func_restricted,
            x0=seed,
            method=minimizer
        )

        if cofs.success:

            tc = cofs.x[0]
            m = cofs.x[1]
            w = cofs.x[2]

            a, b, c1, c2 = self.matrix_equation(observations, tc, m, w)
            c = (c1 ** 2 + c2 ** 2) ** 0.5

            for coef in ['tc', 'm', 'w', 'a', 'b', 'c', 'c1', 'c2']:
                self.coef_[coef] = eval(coef)
            return tc, m, w, a, b, c, c1, c2
        else:
            raise UnboundLocalError
        
    def _get_tc_bounds(self, obs, lower_bound_pct, upper_bound_pct):
    
        t_first = obs[0, 0]
        t_last = obs[0, -1]
        t_delta = t_last - t_first
        pct_delta_min = t_delta * lower_bound_pct
        pct_delta_max = t_delta * upper_bound_pct
        tc_init_min = t_last - pct_delta_min
        tc_init_max = t_last + pct_delta_max
        
        return tc_init_min, tc_init_max


    def lppls(self, t, tc, m, w, a, b, c1, c2):
        return a + np.power(tc - t, m) * (b + ((c1 * np.cos(w * np.log(tc - t))) + (c2 * np.sin(w * np.log(tc - t)))))

    def func_restricted(self, x, *args):
        tc = x[0]
        m = x[1]
        w = x[2]
        obs = args[0]

        a, b, c1, c2 = self.matrix_equation(obs, tc, m, w)

        delta = [self.lppls(t, tc, m, w, a, b, c1, c2) for t in obs[0, :]]
        delta = np.subtract(delta, obs[1, :])
        delta = np.power(delta, 2)

        return np.sum(delta)

    def matrix_equation(self, observations, tc, m, w):
        T = observations[0]
        P = observations[1]
        deltaT = tc - T
        phase = np.log(deltaT)
        fi = np.power(deltaT, m)
        gi = fi * np.cos(w * phase)
        hi = fi * np.sin(w * phase)
        A = np.stack([np.ones_like(deltaT), fi, gi, hi])

        return np.linalg.lstsq(A.T, P, rcond=None)[0].astype('float').tolist()

    def plot_fit(self):
    
        tc, m, w, a, b, c, c1, c2 = self.coef_.values()
        lppls_fit = [self.lppls(t, tc, m, w, a, b, c1, c2) for t in self.observations[0]]

        data = pd.DataFrame({
            'Time': self.observations[0],
            'LPPLS Fit': lppls_fit,
            'Observations': self.observations[1],
        })
        data = data.set_index('Time')
        data.plot(figsize=(14, 8))

    def plot_confidence_indicators(self, res, condition_name, title):
    
        price = self.observations[1, :]
        n = len(price) - len(res)
        pos_conf_lst = [0] * n
        neg_conf_lst = [0] * n
        for r in res:
            pos_true_count = 0
            neg_true_count = 0
            for fits in r:
                if fits['qualified'][condition_name] and fits['sign'] > 0:
                    pos_true_count = pos_true_count + 1
                if fits['qualified'][condition_name] and fits['sign'] < 0:
                    neg_true_count = neg_true_count + 1
            pos_conf_lst.append(pos_true_count / len(r))
            neg_conf_lst.append(neg_true_count / len(r))

        fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, sharex=True, figsize=(15, 12))
        fig.suptitle(title)
        # plot pos bubbles
        ax1_0 = ax1.twinx()
        ax1.plot(price, color='black')
        ax1_0.plot(pos_conf_lst, label='bubble indicator (pos)')

        # plot neg bubbles
        ax2_0 = ax2.twinx()
        ax2.plot(price, color='black')
        ax2_0.plot(neg_conf_lst, label='bubble indicator (neg)')

        # set grids
        ax1.grid(which='major', axis='both', linestyle='--')
        ax2.grid(which='major', axis='both', linestyle='--')

        # set labels
        ax1.set_ylabel('price')
        ax2.set_ylabel('price')

        ax1_0.set_ylabel('bubble indicator (pos)')
        ax2_0.set_ylabel('bubble indicator (neg)')

        ax1_0.legend(loc=2)
        ax2_0.legend(loc=2)

    def mp_compute_indicator(self, workers, window_size=80, smallest_window_size=20, increment=5, max_searches=25,
                             filter_conditions_config=[]):
        obs_copy = self.observations
        obs_copy_len = len(obs_copy[0, :]) - window_size

        func = self._func_compute_indicator

        func_arg_map = [(
            obs_copy[:, i:window_size + i],  # obs
            i,  # n_iter
            window_size,  # window_size
            smallest_window_size,  # smallest_window_size
            increment,  # increment
            max_searches,  # max_searches
            filter_conditions_config,
        ) for i in range(obs_copy_len)]

        pool = multiprocessing.Pool(processes=workers)

        result = pool.map(func, func_arg_map)
        pool.close()

        self.indicator_result = result
        return result

    def _func_compute_indicator(self, args):

        obs, n_iter, window_size, smallest_window_size, increment, max_searches, filter_conditions_config = args

        n_fits = (window_size - smallest_window_size) // increment

        res = []

        for j in range(n_fits):
            obs_shrinking_slice = obs[:, j * increment:window_size + n_iter]

            tc, m, w, a, b, c, c1, c2 = self.fit(obs_shrinking_slice, max_searches, minimizer='SLSQP')

            first = obs_shrinking_slice[0][0]
            last = obs_shrinking_slice[0][-1]

            qualified = {}
            
            for condition in filter_conditions_config:
                for value in condition:
                    tc_min, tc_max = condition[value][0]
                    m_min, m_max = condition[value][1]
                    w_min, w_max = condition[value][2]
                    O_min = condition[value][3]
                    D_min = condition[value][4]

                    tc_init_min, tc_init_max = self._get_tc_bounds(obs_shrinking_slice, tc_min, tc_max)

                    tc_in_range = last - tc_init_min < tc < last + tc_init_max
                    m_in_range = m_min < m < m_max
                    w_in_range = w_min < w < w_max

                    O_in_range = ((w / (2 * np.pi)) * np.log(abs(tc / (tc - last)))) > O_min

                    D_in_range = (m * abs(b)) / (w * abs(c)) > D_min if m > 0 and w > 0 else False

                    if tc_in_range and m_in_range and w_in_range and O_in_range and D_in_range:
                        is_qualified = True
                    else:
                        is_qualified = False

                    qualified[value] = is_qualified

            sign = 1 if b < 0 else -1

            res.append({
                'tc': tc,
                'm': m,
                'w': w,
                'a': a,
                'b': b,
                'c': c,
                'c1': c1,
                'c2': c2,
                'qualified': qualified,
                'sign': sign,
                't1': first,
                't2': last,
            })

        return res
