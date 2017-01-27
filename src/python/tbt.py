import sys, re
import math, cmath
import numpy as np


# Global constants.
X_ = 0; Y_ = 1; Z_ = 2

ss_dim = 6


def sqr(x): return x**2

def printf(format, *args):
    sys.stdout.write(format % args)

def fprintf(outf, format, *args):
    outf.write(format % args)


class lin_opt_type (object):
    def __init__(self):
        self.loc   = []
        self.name  = []
        self.s     = np.zeros(1)
        self.alpha = np.zeros((2, 1))
        self.beta  = np.zeros((2, 1))
        self.nu    = np.zeros((2, 1))
        self.eta   = np.zeros((2, 1))
        self.etap  = np.zeros((2, 1))

    def rd_data(self, file_name):
        alpha = np.zeros((2, 1)); beta = np.zeros((2, 1))
        nu    = np.zeros((2, 1));
        eta   = np.zeros((2, 1)); etap = np.zeros((2, 1));

        prt = False
        inf = open(file_name, 'r')
        if prt: printf('\n')
        for line in inf:
            # Skip comments; lines starting with '#'.
            if line[0] != '#':
                [n, name, s, type,
                 alpha[X_], beta[X_], nu[X_], eta[X_], etap[X_],
                 alpha[Y_], beta[Y_], nu[Y_], eta[Y_], etap[Y_]] \
                 = line.strip('\n').split(',')
                n = int(n); s = float(s)
                for k in range(2):
                    alpha[k] = float(alpha[k]); beta[k] = float(beta[k]);
                    nu[k] = float(nu[k]);
                    eta[k] = float(eta[k]); etap[k] = float(etap[k]);
                self.loc.append(n)
                self.name = np.append(self.name, name)
                self.s = np.append(self.s, s)
                self.alpha = np.append(self.alpha, [alpha[X_], alpha[Y_]],
                                       axis=1)
                self.beta = np.append(self.beta, [beta[X_], beta[Y_]],
                                      axis=1)
                self.nu = np.append(self.nu, [nu[X_], nu[Y_]], axis=1)
                self.eta = np.append(self.eta, [eta[X_], eta[Y_]], axis=1)
                self.etap = np.append(self.etap, [etap[X_], etap[Y_]],
                                      axis=1)
                if prt:
                    printf('%4d, %-15s, %9.5f,'
                           ' %9.5f, %8.5f, %8.5f, %8.5f, %8.5f,'
                           ' %9.5f, %8.5f, %8.5f, %8.5f, %8.5f\n',
                           n, name, s,
                           alpha[X_], beta[X_], nu[X_], eta[X_], etap[X_],
                           alpha[Y_], beta[Y_], nu[Y_], eta[Y_], etap[Y_])
        inf.close()


class bpm_data_type (object):
    def __init__(self):
        self.name = []
        self.loc  = []
        self.data = np.zeros((2, 1, 1))

    def get_loc(self, name, lin_opt):
        k = 0
        while k < len(lin_opt.loc) and name != lin_opt.name[k]:
            k += 1
        return k

    def get_bpm_name(self, name):
        name = re.sub ('-', '_', name).lower()
        return name

    def rd_bpm_names(self, inf, lin_opt):
        prt = False
        n_print = 8
        # Skip 1st line.
        line = inf.readline()
        # Read no of BPMs and no of turns.
        [self.n_bpm, self.n_turn] = inf.readline().strip('\n').split()
        self.n_bpm = int(self.n_bpm)
        self.n_turn = int(self.n_turn)
        # Skip 3rd line.
        line = inf.readline()
        printf('\nno of BPMs = %d, no of turns = %d \n',
               self.n_bpm, self.n_turn)

        self.data.resize((2, self.n_bpm, self.n_turn))

        if prt: printf('\n')
        for j in range(self.n_bpm):
            name = (inf.readline().strip('\n').split())[0]
            name = self.get_bpm_name(name)
            self.name.append(name)
            self.loc.append(self.get_loc(name, lin_opt))
            if prt:
                printf(' %s', self.name[j])
                if (j+1) % n_print == 0: printf('\n')
        if prt and (self.n_bpm % n_print != 0): printf('\n')

    def rd_bpm_data(self, plane, inf):
        prt = False
        n_print = 8
        if prt: printf('\n')
        # Skip line.
        line = inf.readline()
        for k in range(self.n_turn):
            if prt: print('\n')
            data = inf.readline().strip('\n').split()
            for j in range(self.n_bpm-1):
                self.data[plane][j][k] = 1e-3*float(data[j])
                if prt:
                    printf('%10.6f', 1e3*self.data[plane][j][k])
                    if (j+1) % n_print == 0: printf('\n')
	    # Read data for last BPM.
            j = self.n_bpm - 1
            data = inf.readline().strip('\n').split()[0];
            self.data[plane][j][k] = 1e-3*float(data)
            if prt:
                printf('%10.6f\n', 1e3*self.data[plane][j][k])
                if k % n_print != 0: printf('\n')

    def rd_tbt(self, file_name, lin_opt):
        inf = open(file_name, 'r')
        self.rd_bpm_names(inf, lin_opt)
        self.rd_bpm_data(0, inf)
        self.rd_bpm_data(1, inf)
        inf.close()


class est_lin_opt_type (object):
    def __init__(self):
        self.n_stats     = 0e0
        self.alpha_mean  = np.zeros(2)
        self.alpha_sigma = np.zeros(2)
        self.tune_mean   = np.zeros(2)
        self.tune_sigma  = np.zeros(2)
        self.beta        = np.zeros((2, 1))
        self.beta_sum    = np.zeros((2, 1))
        self.beta_sum2   = np.zeros((2, 1))
        self.beta_mean   = np.zeros((2, 1))
        self.beta_sigma  = np.zeros((2, 1))
        self.nu          = np.zeros((2, 1))
        self.dnu_sum     = np.zeros((2, 1))
        self.dnu_sum2    = np.zeros((2, 1))
        self.dnu_mean    = np.zeros((2, 1))
        self.dnu_sigma   = np.zeros((2, 1))
        self.twoJ        = np.zeros((2, 1))
        self.phi         = np.zeros((2, 1))
        self.phi0        = np.zeros((2, 1))

    def zero(self, n):
        self.beta.resize((2, n))
        self.beta_sum.resize((2, n)); self.beta_sum2.resize((2, n))
        self.beta_mean.resize((2, n)); self.beta_sigma.resize((2, n))
        self.nu.resize((2, n))
        self.dnu_sum.resize((2, n)); self.dnu_sum2.resize((2, n))
        self.dnu_mean.resize((2, n)); self.dnu_sigma.resize((2, n))

        for j in range(0, len(self.beta_sum[X_])):
            for k in range(2):
                self.beta_sum[k][j] = 0e0; self.beta_sum2[k][j] = 0e0
                self.dnu_sum[k][j] = 0e0; self.dnu_sum2[k][j] = 0e0

    def get_stats(self, bpm_data, lin_opt):
        prt = False
        dbeta_max = 5.0; dnu_max = 0.05

        if prt:
            printf('\n bpm                A                               '
                   'nu                              dnu\n')
        for j in range(bpm_data.n_bpm):
            for k in range(2):
                get_m_s(self.n_stats, self.beta_sum[k][j],
                        self.beta_sum2[k][j],
                        self.beta_mean[k][j], self.beta_sigma[k][j])
                get_m_s(self.n_stats,
                        self.dnu_sum[k][j], self.dnu_sum2[k][j],
                        self.dnu_mean[k][j], self.dnu_sigma[k][j])

            if prt:
                printf('%3d  [%5.3f+/-%5.3f, %4.3f+/-%5.3f]'
                       '  [%5.3f+/-%5.3f, %4.3f+/-%4.3f]\n',
                       j+1, self.beta_mean[j][X_], self.beta_sigma[j][X_],
                       self.beta_mean[j][Y_], self.beta_sigma[j][Y_],
                       self.dnu_mean[j][X_], self.dnu_sigma[j][X_],
                       self.dnu_mean[j][Y_], self.dnu_sigma[j][Y_])

        outf = open('tbt.out', 'w')

        dbeta = np.zeros(2); dnu = np.zeros(2)
        fprintf(outf, '\n# bpm  s [m]                 beta [m]'
                '                           nu\n')
        for j in range(bpm_data.n_bpm):
            loc = bpm_data.loc[j]
            for k in range(2):
                # dbeta[k] = beta_mean[k][j] - lin_opt.beta[k][loc]
                dbeta[k] = self.beta_mean[k][j]
                if self.beta_sigma[k][j] > dbeta_max:
                    dbeta[k] = 0e0; self.beta_sigma[k][j] = 0e0

                dnu[k] = self.dnu_mean[k][j] \
                         - (lin_opt.nu[k][loc]-int(lin_opt.nu[k][loc]))
                if self.dnu_sigma[k][j] > dnu_max:
                    printf('\nBPM # %d excluded, plane = %d\n', j, k)
                    dnu[k] = 0e0; dnu_sigma[k][j] = 0e0

            printf('%4d %8.3f %7.3f +/- %5.3f %7.3f +/- %5.3f'
                   '%7.3f +/- %5.3f %7.3f +/- %5.3f %7.3f +/- %8.3f\n',
                   j+1, lin_opt.s[loc],
                   dbeta[X_], self.beta_sigma[X_][j],
                   dbeta[Y_], self.beta_sigma[Y_][j],
                   self.dnu_mean[X_][j], self.dnu_sigma[X_][j],
                   self.dnu_mean[Y_][j], self.dnu_sigma[Y_][j],
                   lin_opt.beta[X_][loc], lin_opt.beta[Y_][loc])

        outf.close()


def DFT(x, n, sgn):
    I = complex(0e0, 1e0)
    for j in range(n/2+1):
	X[j] = 0e0
	for k in range(0, n):
	    X[j] += x[2*k]*math.exp(sgn*I*2e0*np.pi*(k*j)/float(n))
    for j in range(n/2):
	x[2*j] = real(X[j]); x[2*j+1] = imag(X[j])


def FFT1(n, x, A, phi, window):
    xi = np.zeros(2*n)
    for i in range(n):
	if window == 1:
	    # Rectangular.
	    xi[2*i] = x[i]
	elif window == 2:
	    # Sine.
	    xi[2*i] =	math.sin(float(i)/float(n-1)*np.pi)*x[i]
	    break
	elif window == 3:
	    # Sine^2.
	    xi[2*i] = sqr(math.sin(flaot(i)/float(n-1)*np.pi))*x[i]
	else:
	    printf('FFT: not implemented\n')
	    exit(1)
	xi[2*i+1] = 0e0
    np.fft.rfft(xi)
    A = np.zeros(2*n); phi = np.zeros(2*n)
    for i in range(n):
	A[i] = math.sqrt(sqr(xi[2*i])+sqr(xi[2*i+1]))*2e0/n
	phi[i] = -math.atan2(xi[2*i+1], xi[2*i])


def FFT2(n, x, X, window):
    xi = np.zeros(2*n)
    for i in range(n):
	if window == 1:
	    # Rectangular.
	    xi[2*i] = x[i]
	elif window == 2:
	    # Sine.
	    xi[2*i] =	math.sin(float(i)/float(n-1)*np.pi)*x[i]
	elif window == 3:
	    # Sine^2.
	    xi[2*i] =	sqr(math.sin(flaot(i)/float(n-1)*np.pi))*x[i]
	else:
	    cout << 'FFT: not implemented' << '\n'
	    exit(1)

	xi[2*i+1] = 0e0
    np.fft.rfft(xi, 1)
    for i in range(0, n):
	X[i] = complex(xi[2*i+1], xi[2*i])


def get_ind(n, k):
    # Spectrum for real signal is irror symmetric at k = (0, n/2).
    if k == 0:
	ind1 = 1; ind3 = 1
    elif k == n/2:
	ind1 = n/2 - 1; ind3 = n/2 - 1
    else:
	ind1 = k - 1; ind3 = k + 1
    return [ind1, ind3]


def get_nu1(n, A, k, window):
    nu = 0e0
    [ind1, ind3] = get_ind(n, k)
    if A[ind3] > A[ind1]:
	A1 = A[k]; A2 = A[ind3]; ind = k
    else:
	A1 = A[ind1]; A2 = A[k]
	# Special case for 0 frequency.
	if k != 0:
            ind = ind1
        else:
            ind = -1
    # Avoid division by zero.
    if A1+A2 != 0e0:
	if (window == 1):
	    nu = (ind+A2/(A1+A2))/n
	elif window == 2:
	    nu = (ind-0.5e0+2e0*A2/(A1+A2))/n
	elif window == 3:
	    nu = (ind-1e0+3e0*A2/(A1+A2))/n
	else:
	    cout << 'get_nu: not defined\n'
    else:
	nu = 0e0
    return nu


def sinc(omega):
    if (omega != 0.0):
        return math.sin(omega)/omega
    else:
        return 1e0


def get_A(n, A, nu, k, window):
    corr = 0e0
    if window == 1:
	corr = sinc(np.pi*(k-nu*n))
    elif window == 2:
	corr = (sinc(np.pi*(k+0.5e0-nu*n))+sinc(np.pi*(k-0.5e0-nu*n)))/2e0
    elif window == 3:
	cout << 'get_A: not implemented\n'
	exit(1)
    else:
	cout << 'get_A: not defined\n'
    return A[k]/corr


def get_alpha(n, X, nu, k, delta, alpha):
    # M. Bertocco, C. Offelli, D. Petri "Analysis of Damped Sinusoidal
    # Signals
    # via a Frequency-Domain Interpolation Algorithm" IEEE 43 (2),
    # 245-250
    # (1994).

    I = complex(0e0, 1e0)
    [ind1, ind3] = get_ind(n, k)
    if abs(X[ind3]) > abs(X[ind1]):
	d = 1; rho = X[ind3]/X[k]
    else:
	d = -1; rho = X[ind1]/X[k]
    z = (1e0-rho)/(1e0-rho*cmath.exp(-I*2e0*np.pi*float(d)/float(n)))
    delta = n*cmath.phase(z)/(2e0*np.pi)
    alpha = n*math.log(abs(z))/(2e0*np.pi)


def get_peak(n, A):
    k = 0
    peak = 0e0
    for ind2 in range(n/2+1):
	[ind1, ind3] = get_ind(n, ind2)
	if (A[ind2] > peak) and (A[ind1] < A[ind2]) and (A[ind2] > A[ind3]):
	    peak = A[ind2]
	    k = ind2
    return k


def get_phi(n,  k,  nu, phi):
    phi_nu = phi[k] - (n*nu-k)*np.pi
    if phi_nu > np.pi:
	phi_nu -= 2.0*np.pi
    elif phi_nu < -np.pi:
	phi_nu += 2.0*np.pi
    return phi_nu


def get_nu2(n,  x, nu, A_nu, phi_nu, delta, alpha, window):
    A = np.zeros(n); phi = np.zeros(n); nu = np.zeros(n)
    FFT1(n, x, A, phi, window)
    k = get_peak(n, A)
    nu = get_nu1(n, A, k, window)
    A_nu = get_A(n, A, nu, k, window)
    phi_nu = get_phi(n, k, nu, phi)
    # Rectangular window.
    X = np.zeros(n, dtype=complex)
    FFT2(n, x, X, 1)
    get_alpha(n, X, nu, k, delta, alpha)


def rm_mean(n, x):
    mean = 0e0
    for i in range(0, n):
	mean += x[i]
    mean /= n
    for i in range(0, n):
	x[i] -= mean


def get_nus(outf, cut, n,  window, bpm_data,  lin_opt,  est_lin_opt):
    prt = False
    sgn = [1, -1]
    beta_pinger = (6.92e0, 6.76e0)

    tunes = np.zeros((bpm_data.n_bpm, 2))

    tune_sum = np.zeros(2); tune_sum2 = np.zeros(2)
    alpha_sum = np.zeros(2); alpha_sum2 = np.zeros(2)
    twoJ_sum = np.zeros(2); twoJ_sum2 = np.zeros(2)
    phi0_sum = np.zeros(2); phi0_sum2 = np.zeros(2)
    for j in range(2):
	tune_sum[j]  = 0e0; tune_sum2[j]  = 0e0
        alpha_sum[j] = 0e0; alpha_sum2[j] = 0e0
        twoJ_sum[j]  = 0e0; twoJ_sum2[j]  = 0e0
	phi0_sum[j]  = 0e0; phi0_sum2[j]  = 0e0

    x = np.zeros(n)
    As = np.zeros((bpm_data.n_bpm, 2)); phis = np.zeros((bpm_data.n_bpm, 2))
    delta = np.zeros(2); alpha = np.zeros(2)
    nus = np.zeros((bpm_data.n_bpm, 2))
    phi0 = np.zeros(2)
    for i in range(bpm_data.n_bpm):
	loc = bpm_data.loc[i]
	for j in range(2):
	    for k in range(cut, n+cut):
		x[k-cut] = bpm_data.data[j][i][k]

	    rm_mean(n, x)

	    get_nu2(n, x, tunes[i][j], As[i][j], phis[i][j], delta[j],
		    alpha[j], window)

	    if sgn[j] < 0:
		phis[i][j] = -phis[i][j]
	    if phis[i][j] < 0e0:
		phis[i][j] += 2e0 * np.pi
	    nus[i][j] = phis[i][j] / (2e0 * np.pi)

	    tune_sum[j] += tunes[i][j]; tune_sum2[j] += sqr(tunes[i][j])
	    alpha_sum[j] += alpha[j]; alpha_sum2[j] += sqr(alpha[j])

	    twoJ = sqr(As[i][j])/lin_opt.beta[j][loc]
	    twoJ_sum[j] += twoJ; twoJ_sum2[j] += sqr(twoJ)

	    phi0[j] = (nus[i][j]-(lin_opt.nu[j][loc]
                                  -int(lin_opt.nu[j][loc])))*2e0*np.pi
	    if phi0[j] < 0e0:
		phi0[j] += 2e0*np.pi
	    phi0_sum[j] += phi0[j]; phi0_sum2[j] += sqr(phi0[j])

	# if (prt) printf('[%8.6f, %8.6f]\n', tunes[i][X_],
	# tunes[i][Y_])

    twoJ_mean = np.zeros(2); twoJ_sigma = np.zeros(2)
    phi0_mean = np.zeros(2); phi0_sigma = np.zeros(2)
    for j in range(2):
	twoJ_mean[j] = twoJ_sum[j]/bpm_data.n_bpm
        twoJ_sigma[j] = math.sqrt((bpm_data.n_bpm*twoJ_sum2[j]
                                   -sqr(twoJ_sum[j]))
		                  /(bpm_data.n_bpm*(bpm_data.n_bpm-1e0)))

	phi0_mean[j] = phi0_sum[j]/bpm_data.n_bpm
	# phi0_sigma[j] = math.sqrt((bpm_data.n_bpm*phi0_sum2[j]
        #                            -sqr(phi0_sum[j]))
	# 	                  /(bpm_data.n_bpm*(bpm_data.n_bpm-1e0)))

    printf('\ntwoJ = [%11.3e+/-%11.3e, %11.3e+/-%11.3e]'
           ', phi0 = [%9.3e]+/-%9.3f, %9.3f+/-%9.3f]\n',
           twoJ_mean[X_], twoJ_sigma[X_], twoJ_mean[Y_], twoJ_sigma[Y_],
           phi0_mean[X_], phi0_sigma[X_], phi0_mean[Y_], phi0_sigma[Y_])
    printf('A0   = [%9.3f, %9.3f] mm\n',
           1e3*math.sqrt(twoJ_mean[X_]*beta_pinger[X_]),
           1e3*math.sqrt(twoJ_mean[Y_]*beta_pinger[Y_]))

    # Normalize.
    if prt:
        printf('\n bpm        A               nu            nu (model)\n')
    dnu = np.zeros(2)
    for i in range(bpm_data.n_bpm):
	loc = bpm_data.loc[i]
	for j in range(2):
	    beta = sqr(As[i][j])/twoJ_mean[j]

	    nus[i][j] -= phi0_mean[j]/(2e0*np.pi)
	    if nus[i][j] < 0e0:	nus[i][j] += 1e0

	    dnu[j] = nus[i][j]-(lin_opt.nu[j][loc] -int(lin_opt.nu[j][loc]))
	    if dnu[j] < -0.5e0: dnu[j] += 1e0
	    if dnu[j] > 0.5e0:	dnu[j] -= 1e0

	    est_lin_opt.beta_sum[j][i] += beta
	    est_lin_opt.beta_sum2[j][i] += sqr(beta)
	    est_lin_opt.dnu_sum[j][i] += dnu[j]
	    est_lin_opt.dnu_sum2[j][i] += sqr(dnu[j])

	fprintf(outf, '%4d %7.3f %8.3f %8.3f\n',
                i+1, lin_opt.s[loc], dnu[X_], dnu[Y_])

	if prt:
	    fprintf('%3d  [%6.3f, %5.3f]  [%6.3f, %5.3f]  [%6.3f, %5.3f]\n',
                    i+1, 1e3*As[i][X_], 1e3*As[i][Y_],
                    nus[i][X_], nus[i][Y_],
                    lin_opt.nu[X_][loc]-int(lin_opt.nu[X_][loc]),
                    lin_opt.nu[Y_][loc]-int(lin_opt.nu[Y_][loc]))

    for j in range(2):
	est_lin_opt.tune_mean[j] = tune_sum[j]/bpm_data.n_bpm
	if sgn[j] < 0:
	    est_lin_opt.tune_mean[j] = 1e0 - est_lin_opt.tune_mean[j]
	est_lin_opt.tune_sigma[j] = \
            math.sqrt((bpm_data.n_bpm*tune_sum2[j]-sqr(tune_sum[j]))
		   /(bpm_data.n_bpm*(bpm_data.n_bpm-1e0)))

	est_lin_opt.alpha_mean[j] = alpha_sum[j]/bpm_data.n_bpm
	est_lin_opt.alpha_sigma[j] = \
	    math.sqrt((bpm_data.n_bpm*alpha_sum2[j]-sqr(alpha_sum[j]))
		   /(bpm_data.n_bpm*(bpm_data.n_bpm-1e0)))

    printf('\nnu    = [%8.6f+/-%8.6f, %8.6f+/-%8.6f]\n',
           est_lin_opt.tune_mean[X_], est_lin_opt.tune_sigma[X_],
           est_lin_opt.tune_mean[Y_], est_lin_opt.tune_sigma[Y_])
    printf('alpha = [%8.6f+/-%8.6f, %8.6f+/-%8.6f]\n',
           est_lin_opt.alpha_mean[X_], est_lin_opt.alpha_sigma[X_],
           est_lin_opt.alpha_mean[Y_], est_lin_opt.alpha_sigma[Y_])

    printf('%8.5f %8.5f\n', nus[6][X_]-nus[5][X_], nus[6][Y_]-nus[5][Y_])


def get_m_s(n, sum, sum2, mean, sigma):
    mean = sum/n; sigma = math.sqrt((n*sum2-sqr(sum))/(n*(n-1e0)))


def prt_FFT(n, cut, x, y, window):
    outf = open('sls.out', 'w')
    x1 = np.zeros((2, n))
    for j in range(cut, n+cut):
	x1[X_][j-cut] = x[j]; x1[Y_][j-cut] = y[j]
	fprintf(outf, '%5d %11.3e %11.3e\n', j+1, x[j], y[j])
    outf.close()

    A = np.zeros((2, n)); phi = np.zeros((2, n))
    for k in range(0, 2):
	FFT1(n, x1[k], A[k], phi[k], window)

    outf = open('sls_fft.out', 'w')
    for k in range(n/2+1):
        fprintf(outf, '%5d %9.3e %9.3e %9.3e\n',
                k+1, float(k)/float(n), A[X_][k], A[Y_][k])
    outf.close()


def get_b1ob2_dnu(n, ps1, ps2):
    # Estimate beta_1/beta_2 and Dnu by tracking data from two adjacent
    # BPMs.

    printf('\n')
    b1ob2 = np.zeros(n); dnu = np.zeros(n)
    for j in range(2):
	x1_sqr = 0e0; x2_sqr = 0e0; x1x2 = 0e0
	for k in range(n):
	    x1_sqr += sqr(ps1[k][2*j]); x2_sqr += sqr(ps2[k][2*j])
	    x1x2 += ps1[k][2*j]*ps2[k][2*j]

	x1_sqr /= n; x2_sqr /= n; x1x2 /= n;

	b1ob2[j] = x1_sqr/x2_sqr
	dnu[j] = math.acos(x1x2/math.sqrt(x1_sqr*x2_sqr))/(2e0*np.pi)

	printf('b1ob2 = %10.3e, dnu = %10.3e\n', b1ob2[j], dnu[j])
    return [b1ob2, dnu]


def ss_est(n, bpm1, bpm2, bpm_data, lin_opt):
    ps1 = np.zeros((n, ss_dim)); ps2 = np.zeros((n, ss_dim))
    for j in range(0, n):
	for k in range(2):
	    ps1[j][k] = bpm_data.data[k][bpm1-1][j]
	    ps2[j][k] = bpm_data.data[k][bpm2-1][j]

    [b1ob2, dnu] = get_b1ob2_dnu(n, ps1, ps2)

    loc1 = bpm_data.loc[bpm1-1]; loc2 = bpm_data.loc[bpm2-1]

    printf('\nb1ob2 = %10.3e, dnu =  %10.3e\n',
           lin_opt.beta[X_][loc1]/lin_opt.beta[X_][loc2],
           lin_opt.nu[X_][loc2]-lin_opt.nu[X_][loc1])
    printf('b1ob2 =  %10.3e, dnu =  %10.3e\n',
           lin_opt.beta[Y_][loc1]/lin_opt.beta[Y_][loc2],
	   lin_opt.nu[Y_][loc2]-lin_opt.nu[Y_][loc1])


def prt_name(outf, name):
    strlen = len(name); j = 0
    while (j < strlen) and (name[j] != ' '):
	fprintf(outf, '%c' % (name[j]))
	j += 1
    fprintf(outf, ',')
    for k in range(j, strlen):
	fprintf(outf, '%c' % (name[k]))


def main():
    bpm_data    = bpm_data_type()
    lin_opt     = lin_opt_type()
    est_lin_opt = est_lin_opt_type()

    home_dir = '/home/johan/git_repos/projects/src/sls_tbt/'

    # sls_ri_f6cwo_20.435_8.737_gset7
    file_name = home_dir + 'linlat_maxlab.out'

    lin_opt.rd_data(file_name)

    # T-b-T data.
    window = 2; cut = 0*5; n_turn = 2*1024; bpm1 = 6

    bpm_data.rd_tbt(home_dir+'tbt_090513_215959.log', lin_opt)

    prt_FFT(n_turn, cut, bpm_data.data[X_][bpm1-1],
	    bpm_data.data[Y_][bpm1-1], window)

    # Linear optics.
    window = 2; cut = 0; n_turn = 2048

    est_lin_opt.zero(len(lin_opt.beta[X_]))

    outf = open('tbt_optics.out', 'w')

    est_lin_opt.n_stats = 1
    bpm_data.rd_tbt(home_dir+'tbt_090513_215619.log', lin_opt)
    get_nus(outf, cut, n_turn, window, bpm_data, lin_opt, est_lin_opt)

    est_lin_opt.n_stats += 1
    bpm_data.rd_tbt(home_dir+'tbt_090513_215631.log', lin_opt)
    get_nus(outf, cut, n_turn, window, bpm_data, lin_opt, est_lin_opt)

    est_lin_opt.n_stats += 1
    bpm_data.rd_tbt(home_dir+'tbt_090513_215652.log', lin_opt)
    get_nus(outf, cut, n_turn, window, bpm_data, lin_opt, est_lin_opt)

    outf.close()

    est_lin_opt.get_stats(bpm_data, lin_opt)

    # Phase space.
    n_turn = 2048; bpm1 = 5; bpm2 = 6

    bpm_data.rd_tbt(home_dir+'tbt_090513_215619.log', lin_opt)

    ss_est(n_turn, bpm1, bpm2, bpm_data, lin_opt)


main()