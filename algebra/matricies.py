import functools
from algebra import base
from algebra import polynomials
import itertools

#===SUMMARY===

#==DATA STRUCTURE==
#put numbers into a matrix

#==OVER AN ED==
#=SPAN= (ModuleSpan)
#objects are submodules
#=QUOTIENT= (ModuleQuotient)
#objects are elements mod submodules
#isomorphism type from smith normal form (SNF)

#==OVER A FIELD== (SPECIAL CASE OF ED)
#=SPAN= (VectorSpan)
#objects are subspaces
#=quotient= (VectorQuotient)
#QUOTIENT are vectors mod subspace
#isomorphism type from dimention = how many diagonal entries in the SNF

#===APPLICATIONS===
#homology
#integer systems of equations
#linear systems of equations
#jordan normal form
#character tables
#algebraic numbers

def assoc_opp(f):
    def new_f(cls, values):
        ans = values[0]
        for value in values[1:]:
            ans = f(cls, ans, value)
        return ans
    return new_f


class SizeMismatch(Exception):
    pass

class NoSolution(Exception):
    pass



class MatrixBase(base.MathsSet):
    base_ring = None
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols


@functools.cache
def MatrixOver(ring):
    assert issubclass(ring, base.Ring)
    class Matrix(MatrixBase):
        @classmethod
        def test_axioms(cls, test):
            super().test_axioms(test)
                
        @classmethod
        def typestr(cls):
            return f"Mat({ring})"

        @classmethod
        def sum(cls, rows, cols, mats):
            ans = cls.zero(rows, cols)
            for mat in mats:
                ans += mat
            return ans

        @classmethod
        @assoc_opp
        def join_rows(cls, mat1, mat2):
            assert (cols := mat1.cols) == mat2.cols
            return cls(mat1.rows + mat2.rows, cols, mat1.entries + mat2.entries)
        @classmethod
        @assoc_opp
        def join_cols(cls, mat1, mat2):
            assert (rows := mat1.rows) == mat2.rows
            return cls(rows, mat1.cols + mat2.cols, [mat1.entries[r] + mat2.entries[r] for r in range(rows)])
        @classmethod
        @assoc_opp
        def join_diag(cls, mat1, mat2):
            assert type(mat1) == type(mat2) == cls
            bl_zeros = cls(mat2.rows, mat1.cols, [[0 for c in range(mat1.cols)] for r in range(mat2.rows)])
            tr_zeros = cls(mat1.rows, mat2.cols, [[0 for c in range(mat2.cols)] for r in range(mat1.rows)])
            return cls.join_cols([cls.join_rows([mat1, bl_zeros]), cls.join_rows([tr_zeros, mat2])])

        @classmethod
        def eye(cls, n):
            return cls(n, n, [[(1 if r == c else 0) for c in range(n)] for r in range(n)])
        @classmethod
        def zero(cls, r, c = None):
            if c is None:
                c = r
            return cls(r, c, [[0 for _ in range(c)] for _ in range(r)])

        @classmethod
        def init_cls(cls):
            super().init_cls()
            cls.base_ring = ring

        @classmethod
        def convert(cls, x):
            try:
                return super().convert(x)
            except NotImplementedError:
                pass

            if isinstance(x, MatrixBase):
                try:
                    return cls(x.rows, x.cols, [[cls.base_ring.convert(x[r, c]) for c in range(x.cols)] for r in range(x.rows)])
                except NotImplementedError:
                    pass
            raise NotImplementedError()

        def __init__(self, rows, cols, entries):
            super().__init__(rows, cols)
            entries = tuple(tuple(ring.convert(x) for x in row) for row in entries)
            assert len(entries) == rows
            for row in entries:
                assert len(row) == cols
            self.entries = entries

        def __getitem__(self, pos):
            assert type(pos) == tuple and len(pos) == 2
            r, c = pos
            return self.entries[r][c]

        def __str__(self):
            strs = [[str(self[r, c]) for c in range(self.cols)] for r in range(self.rows)]
            lens = [max(len(strs[r][c]) for r in range(self.rows)) for c in range(self.cols)]
            strs = [[strs[r][c] + " " * (lens[c] - len(strs[r][c])) for c in range(self.cols)] for r in range(self.rows)]

            def brac(r):
                if self.rows == 1:
                    return "["
                else:
                    if r == 0:
                        return "/"
                    elif r == self.rows - 1:
                        return "\\"
                    else:
                        return "|"
            def flip(b):
                return {"[" : "]", "/" : "\\", "\\" : "/", "|" : "|"}[b]
                
            return "\n".join(brac(r) + " ".join(strs[r][c] for c in range(self.cols)) + flip(brac(r)) for r in range(self.rows))
        
        def __repr__(self):
            return f"Mat({ring}, [{', '.join('[' + ', '.join(repr(x) for x in row) + ']' for row in self.entries)}])"

        def equal(self, other):
            assert (cls := type(self)) == type(other)
            if (rows := self.rows) == other.rows:
                if (cols := self.cols) == other.cols:
                    for r in range(rows):
                        for c in range(cols):
                            if self[r, c] != other[r, c]:
                                return False
                    return True
            return False
        def add(self, other):
            assert (cls := type(self)) == type(other)
            if (rows := self.rows) == other.rows and (cols := self.cols) == other.cols:
                return cls(rows, cols, [[self[r, c] + other[r, c] for c in range(cols)] for r in range(rows)])
            else:
                raise SizeMismatch("Matricies must have the same dimentions for addition")
        def neg(self):
            return type(self)(self.rows, self.cols, [[-self[r, c] for c in range(self.cols)] for r in range(self.rows)])
        def mul(self, other):
            assert (cls := type(self)) == type(other)
            if (mids := self.cols) == other.rows:
                rows = self.rows
                cols = other.cols
                return cls(rows, cols, [[ring.sum([self[r, m] * other[m, c] for m in range(mids)]) for c in range(cols)] for r in range(rows)])
            else:
                raise SizeMismatch("Matricies dont have compatible dimention for matrix multiplication")
            
        def scalarmul_right(self, other):
            assert isinstance(other, ring)
            return type(self)(self.rows, self.cols, [[self[r, c] * other for c in range(self.cols)] for r in range(self.rows)])
        def scalarmul_left(self, other):
            assert isinstance(other, ring)
            return type(self)(self.rows, self.cols, [[other * self[r, c] for c in range(self.cols)] for r in range(self.rows)])

        def __hash__(self):
            return hash(self.entries)
        def __eq__(self, other):
            if type(self) == type(other):
                return self.equal(other)
            try:
                other = self.convert(other)
            except NotImplementedError:
                pass
            else:
                return self.equal(other)
            return False
        def __add__(self, other):
            if type(self) == type(other):
                return self.add(other)
            try:
                other = self.convert(other)
            except NotImplementedError:
                pass
            else:
                return self.add(other)
            return NotImplemented
        def __radd__(self, other):
            try:
                other = self.convert(other)
            except NotImplementedError:
                pass
            else:
                return other.add(self)
            return NotImplemented
        def __neg__(self):
            return self.neg()
        def __sub__(self, other):
            if type(self) == type(other):
                return self.add(other.neg())
            try:
                other = self.convert(other)
            except NotImplementedError:
                pass
            else:
                return self.add(other.neg())
            return NotImplemented
        def __rsub__(self, other):
            if type(self) == type(other):
                return other.add(self.neg())
            try:
                other = self.convert(other)
            except NotImplementedError:
                pass
            else:
                return other.add(self.neg())
            return NotImplemented
        def __mul__(self, other):
            if type(self) == type(other):
                return self.mul(other)
            try:
                other = self.convert(other)
            except NotImplementedError:
                pass
            else:
                return self.mul(other)
            try:
                other = ring.convert(other)
            except NotImplementedError:
                pass
            else:
                return self.scalarmul_right(other)
            return NotImplemented
        def __rmul__(self, other):
            if type(self) == type(other):
                return other.mul(self)
            try:
                other = self.convert(other)
            except NotImplementedError:
                pass
            else:
                return other.mul(self)
            try:
                other = ring.convert(other)
            except NotImplementedError:
                pass
            else:
                return self.scalarmul_left(other)
            return NotImplemented
        def __pow__(self, other):
            cls = type(self)
            if (n := self.rows) == self.cols:
                if type(other) == int:
                    if other < 0:
                        return (self ** (-other)).inverse()
                    elif other == 0:
                        return cls.eye(n)
                    elif other == 1:
                        return self
                    elif other == 2:
                        return self * self
                    else:
                        q, r = divmod(other, 2)
                        return (self ** q) ** 2 * self ** r
            return NotImplemented

        def transpose(self):
            return type(self)(self.cols, self.rows, [[self[c, r] for c in range(self.rows)] for r in range(self.cols)])
        def flip_rows(self):
            return type(self)(self.rows, self.cols, [[self[self.rows - r - 1, c] for c in range(self.cols)] for r in range(self.rows)])
        def flip_cols(self):
            return type(self)(self.rows, self.cols, [[self[r, self.cols - c - 1] for c in range(self.cols)] for r in range(self.rows)])
        def row(self, r):
            return type(self)(1, self.cols, [self.entries[r]])
        def col(self, c):
            return self.transpose().row(c).transpose()
        def minor(self, row = None, col = None):
            return type(self)(self.rows if row is None else self.rows - 1, self.cols if col is None else self.cols - 1, [[self[r, c] for c in range(self.cols) if c != col] for r in range(self.rows) if r != row])

        def row_swap(self, r1, r2): #r1 <-> r2
            assert type(r1) == int and 0 <= r1 < self.rows
            assert type(r2) == int and 0 <= r2 < self.rows
            assert r1 != r2
            def perm(r):
                if r == r1:
                    return r2
                elif r == r2:
                    return r1
                else:
                    return r
            return type(self)(self.rows, self.cols, [[self[perm(r), c] for c in range(self.cols)] for r in range(self.rows)])
        def row_mult(self, r1, m): #r1 -> m * r1
            assert type(r1) == int and 0 <= r1 < self.rows
            m = ring.convert(m)
            return type(self)(self.rows, self.cols, [[(m * self[r1, c] if r == r1 else self[r, c]) for c in range(self.cols)] for r in range(self.rows)])
        def row_add(self, r1, r2, m): #r1 -> r1 + m * r2
            assert r1 != r2
            assert type(r1) == int and 0 <= r1 < self.rows
            assert type(r2) == int and 0 <= r2 < self.rows
            m = ring.convert(m)
            return type(self)(self.rows, self.cols, [[(self[r1, c] + m * self[r2, c] if r == r1 else self[r, c]) for c in range(self.cols)] for r in range(self.rows)])

        def col_swap(self, c1, c2): #c1 <-> c2
            return self.transpose().row_swap(c1, c2).transpose()
        def col_mult(self, c1, m): #c1 -> m * c1
            return self.transpose().row_mult(c1, m).transpose()
        def col_add(self, c1, c2, m): #c1 -> c1 + m * c2
            return self.transpose().row_add(c1, c2, m).transpose()

        @functools.lru_cache()
        def hermite_algorithm(self):
            if not issubclass(ring, base.EuclideanDomain):
                raise Exception(f"Cant do hermite algorithm over non-ED {ring} (yet)")
            #put the matrix into hermite normal form / reduced row echelon form
            #this form is unique for a given matrix
            
            #return U, det(U), pivots, H such that U * self == H
            #U is invertible
            #det(U) is det(U) (obviously)
            #H is in hermite normal form
            #pivots is a tuple of the columns of the pivots of H

            #algorithm idea: cancel columns with analouge of euclids algorithm
            #when the matrix is over a field, this is guassian elimination

            n = self.rows
            U = type(self).eye(n)
            H = self
            pivots = []
            det_U = ring.int(1)
            
            r = 0
            c = 0
            while True:
                while True:
                    #if the column is all zero, skip it
                    non_zero = [br for br in range(r, n) if H[br, c] != 0]
                    if len(non_zero) == 0:
                        c += 1
                        break
                    else:
                        #find non-zero element in col c below r with minimal norm
                        min_r = min(non_zero, key = lambda br : H[br, c].norm())
                        if min_r != r:
                            H = H.row_swap(r, min_r)
                            U = U.row_swap(r, min_r)
                            det_U = -det_U
                        
                        if all(H[br, c] == 0 for br in range(r + 1, n)):
                            #if all elements below r are zero, then reduce all elements above r and continue
                            for ar in range(r):
                                if H[ar, c] != 0:
                                    m = -(H[ar, c] // H[r, c])
                                    H = H.row_add(ar, r, m)
                                    U = U.row_add(ar, r, m)
                            #make sure: if pivot elements are units, then they are 1
                                    
                            u, _ = H[r, c].factor_favorite_associate()
                            v = u.recip()
                            H = H.row_mult(r, v)
                            U = U.row_mult(r, v)
                            det_U *= v
                                
                            pivots.append(c)
                            r += 1
                            c += 1
                            break

                        #subtract multiples of the minimal element to reduce all other norms in the column below r (bit like euclids algorithm)
                        for br in range(r + 1, n):
                            m = -(H[br, c] // H[r, c])
                            H = H.row_add(br, r, m)
                            U = U.row_add(br, r, m)
                            
                if r >= H.rows or c >= H.cols:
                    assert U * self == H
                    return U, det_U, tuple(pivots), H

        def hermite_normal_form(self):
            return self.hermite_algorithm()[3]
        
        def inverse(self):
            assert (n := self.rows) == self.cols
            U, det_U, pivots, H = self.hermite_algorithm()
            if H == type(self).eye(n):
                return U
            else:
                raise Exception("Matrix is not invertible")

        @functools.lru_cache()
        def smith_algorithm(self):
            if not issubclass(ring, base.EuclideanDomain):
                raise Exception(f"Cant do smith algorithm over non-ED {ring}")
            #find invertible S, T such that S * self * T is in smith normal form

            #idea:
            #for each diagonal point
            # - put the element of smallest norm into that spot
            # - reduce others in the row and column
            # - repeat until all are zero
            
            cls = type(self)
            
            S = cls.eye(self.rows)
            A = self
            T = cls.eye(self.cols)
            k = 0 #which diagonal are we doing rn

            while True:
                #if the matrix is all zero, its already in smith normal form
                non_zero = [(r, c) for r, c in itertools.product(range(k, self.rows), range(k, self.cols)) if A[r, c] != 0]
                if len(non_zero) == 0:
                    return S, A, T
                else:
                    #seach for the non-zero element of minimal norm
                    r, c = min(non_zero, key = lambda pos : A[pos].norm())

                    #place it in the top left of A
                    if r != k:
                        A = A.row_swap(r, k)
                        S = S.row_swap(r, k)
                    if c != k:
                        A = A.col_swap(c, k)
                        T = T.col_swap(c, k)

                    #find non-zero elements in the top row and first column (excluding the top left point)
                    non_zero_row = [r for r in range(k + 1, self.rows) if A[r, k] != 0]
                    non_zero_col = [c for c in range(k + 1, self.cols) if A[k, c] != 0]

                    if len(non_zero_row) == 0 and len(non_zero_col) == 0:
                        #if there are none, then euclidian algorithm is complete

                        #put diagonal elements into standard associate form (e.g. for Z, make them positive. for fields, make them 1)
                        u, _ = A[k, k].factor_favorite_associate()
                        v = u.recip()
                        A = A.row_mult(k, v)
                        S = S.row_mult(k, v)

                        #now we want all other elements to be multiples of this top left element
                        for r, c in itertools.product(range(k + 1, self.rows), range(k + 1, self.cols)):
                            if A[r, c] % A[k, k] != 0:
                                #if not, then fiddle about a bit and do a single euclid to reduce the norm of this element
                                A = A.row_add(r, k, 1)
                                S = S.row_add(r, k, 1)

                                m = -(A[r, c] // A[r, k])
                                A = A.col_add(c, k, m)
                                T = T.col_add(c, k, m)

                                #now call smith algorithm on this new matrix with smaller norms appearing
                                #will terminate as new top left norm must cannot decrease forever
                                S_prime, A, T_prime = A.smith_algorithm()
                                S = S_prime * S
                                T = T * T_prime
                                return S, A, T

                        #if they are, then move on to a sub matrix or return if we are done
                        k += 1
                        if k >= self.rows or k >= self.cols:
                            return S, A, T
                    else:
                        #if there are non-zero elements, do some euclids to reduce their norm and repeat
                        for r in non_zero_row:
                            m = -(A[r, k] // A[k, k])
                            A = A.row_add(r, k, m)
                            S = S.row_add(r, k, m)
                            
                        for c in non_zero_col:
                            m = -(A[k, c] // A[k, k])
                            A = A.col_add(c, k, m)
                            T = T.col_add(c, k, m)
                        
        def smith_normal_form(self):
            return self.smith_algorithm()[1]
        def smith_diagonal(self):
            snf = self.smith_normal_form()
            return tuple(snf[i, i] for i in range(min(self.rows, self.cols)))

        def rank(self):
            return len(self.hermite_algorithm()[2])
        def trace(self):
            assert (n := self.rows) == self.cols
            return ring.sum([self[i, i] for i in range(n)])
        def det(self):
            assert (n := self.rows) == self.cols
            U, det_U, pivots, H = self.hermite_algorithm()
            #U * self == H
            #det(H) = product of diagonals
            #det_U is given
            # => det(self) = det(H) / det(U)
            return ring.product([H[i, i] for i in range(n)]) / det_U

        def row_span(self):
            return SpanOver(ring)(1, self.cols, [self.row(r) for r in range(self.rows)])
        def col_span(self):
            return SpanOver(ring)(self.rows, 1, [self.col(c) for c in range(self.cols)])
        def row_kernel(self):
            U, _, pivs, H = self.hermite_algorithm()
            return SpanOver(ring)(1, self.rows, [U.row(r) for r in range(len(pivs), self.rows)])
        def col_kernel(self):
            return self.transpose().row_kernel().transpose()

        def col_solve(self, vec):
            #solve self * x = vec for x
            assert self.cols == vec.rows and vec.cols == 1
            U, det_U, pivots, H = self.hermite_algorithm()
            
            mat = type(self).join_cols([self.col(c) for c in range(self.cols)] + [-vec])
            ker_basis = mat.col_kernel().basis
            g, coeffs = ring.xgcd_list([b[self.cols, 0] for b in ker_basis])
            if g.is_unit():
                coeffs = [c / g for c in coeffs]
            else:
                raise NoSolution("No solution")

            sol = Matrix.sum(self.cols + 1, 1, [coeffs[i] * ker_basis[i] for i in range(len(ker_basis))])
            sol = sol.minor(row = self.cols)
            assert self * sol == vec
            return sol

        def char_mat(self):
            assert (n := self.rows) == self.cols
            polyring = polynomials.PolyOver(ring)
            Pmat = MatrixOver(polyring)
            pself = Pmat(self.rows, self.cols, [[polyring.convert(self[r, c]) for c in range(self.cols)] for r in range(self.rows)])
            return polyring.var() * Pmat.eye(n) - pself
        def min_poly(self):
            return self.char_mat().smith_diagonal()[-1]
        def char_poly(self):
            return polynomials.PolyOver(ring).product(self.char_mat().smith_diagonal())


    if issubclass(ring, base.Field):
        field = ring
        class Matrix(Matrix):
            @classmethod
            def change_of_basis_matrix(cls, A, B):
                assert (n := A.rows) == A.rows == B.cols == B.cols
                #find change of basis matrix M such that AM = MB

                #plan:
                #put both A and B into jcf.
                #if jcf disagree, no such M exists
                #if jcf agree, compose change of basis matricies for jcf
                raise NotImplementedError()

            @functools.cache
            def eigen_val_list(self):
                return tuple(field.AlgebraicClosure.root_list(self.char_poly()))
            @functools.cache
            def eigen_val_powers(self):
                return dict(field.AlgebraicClosure.root_powers(self.char_poly()))          

            #for each eigen value a, the subspace of eigen vectors with eigen value a
            @functools.cache
            def eigen_col_spaces(self):
                assert (n := self.rows) == self.cols
                return {x : (self - MatrixOver(field.AlgebraicClosure).eye(n) * x).col_kernel() for x in self.eigen_val_powers().keys()}                             
            @functools.cache
            def eigen_row_spaces(self):
                assert (n := self.rows) == self.cols
                return {x : (self - MatrixOver(field.AlgebraicClosure).eye(n) * x).row_kernel() for x in self.eigen_val_powers().keys()}

            #these form a set of vectorspaces whose direct sum is R^n
            @functools.cache
            def general_eigen_col_spaces(self):
                assert (n := self.rows) == self.cols
                return {x : ((self - MatrixOver(field.AlgebraicClosure).eye(n) * x) ** p).col_kernel() for x, p in self.eigen_val_powers().items()}
            @functools.cache
            def general_eigen_row_spaces(self):
                assert (n := self.rows) == self.cols
                return {x : ((self - MatrixOver(field.AlgebraicClosure).eye(n) * x) ** p).row_kernel() for x, p in self.eigen_val_powers().items()}

            @functools.lru_cache()
            def jordan_algorithm_unordered(self):
                #compute jordan blocks and change of basis matrices for each block
                raise NotImplementedError()

            def jordan_algorithm_ordered(self, eigen_value_order = None):
                if eigen_value_order is None:
                    pass
                raise NotImplementedError()

            def jordan_canonical_form(self, eigen_value_order = None):
                raise NotImplementedError()

    if False:
        #old implementation
        #use this to write jcf stuff
        class OldEigenMatrix(Matrix):            
            @functools.cache
            def eigen_val_list(self):
                return tuple(self.char_poly().roots())
            @functools.cache
            def eigen_val_powers(self):
                eigen_values = {}
                for x in self.eigen_val_list():
                    if not x in eigen_values:
                        eigen_values[x] = 0
                    eigen_values[x] += 1
                return eigen_values

            @functools.cache
            def eigen_col_spaces(self):
                algcls = polycls.algcls
                assert (n := self.rows) == self.cols
                return {x : (self._lift_weird(algcls, self.polycls.as_root) - MatrixOver(algcls).Identity(n) * x).col_kernel() for x in self.eigen_val_list()}                             
            @functools.cache
            def eigen_row_spaces(self):
                algcls = polycls.algcls
                assert (n := self.rows) == self.cols
                return {x : (self._lift_weird(algcls, self.polycls.as_root) - MatrixOver(algcls).Identity(n) * x).row_kernel() for x in self.eigen_val_list()}

            #these form a set of vectorspaces whose direct sum is R^n
            @functools.cache
            def general_eigen_col_spaces(self):
                algcls = polycls.algcls
                assert (n := self.rows) == self.cols
                return {x : ((self._lift_weird(algcls, self.polycls.as_root) - MatrixOver(algcls).Identity(n) * x) ** p).col_kernel() for x, p in self.eigen_val_powers().items()}
            @functools.cache
            def general_eigen_row_spaces(self):
                algcls = polycls.algcls
                assert (n := self.rows) == self.cols
                return {x : ((self._lift_weird(algcls, self.polycls.as_root) - MatrixOver(algcls).Identity(n) * x) ** p).row_kernel() for x, p in self.eigen_val_powers().items()}

            @functools.cache
            def _jcf_info(self):
                assert (n := self.rows) == self.cols
                algcls = polycls.algcls

                e_vals = list(set(self.eigen_val_list()))
                e_pows = self.eigen_val_powers()
                e_gesp = self.general_eigen_col_spaces()

                #first find basis where T is block diagonal & each block has a single eigen value
                T = self._lift_weird(algcls, self.polycls.as_root)

                basis = []
                for x in e_vals:
                    basis.extend(e_gesp[x].basis)
                B = MatrixOver(algcls).join_cols(basis)
                assert n == B.rows == B.cols
                T_B = B ** -1 * T * B
                E_blocks = T_B.split_block_diag([e_pows[x] for x in e_vals], [e_pows[x] for x in e_vals])
                block_info = {}
                for idx in range(len(e_vals)):
                    T = E_blocks[idx]
                    x = e_vals[idx]
                    n = e_pows[x]
                    #now we are reduced to finding JCF of T with all eigen values equal to x
                    S = T - MatrixOver(algcls).Identity(n) * x
                    #S has e.val 0 repeated n times, can then use its kernel

                    def get_S_jcf_bases(S, V):
                        #return a jcf basis of S acting on V
                        n = V.dimention
                        if n == 0:
                            return []
                        if n == 1:
                            return [[V.basis[0]]]
                        else:
                            new_vecs = [] #keep track of the vectors we add this time round
                            
                            #let W be the image of S acting on V
                            W = S * V
                            #dim W is less than dim V since S has an eigen value of 0 - some direction gets sent to 0
                            assert W.dimention < V.dimention
                            #new find the jcf basis of S acting on W
                            W_bases = get_S_jcf_bases(S, W)
                            #now extend to a basis of V by:
                            #1) adding the preimages of each previous W_basis vector under S
                            #2) extending what is left to include ker(S)

                            V_bases = [[w for w in W_basis] for W_basis in W_bases]
                            #1)
                            for i in range(len(W_bases)):
                                w = W_bases[i][-1]
                                V_bases[i].append(S.col_solve(w, V))

                            #2)                        
                            S_ker = S.col_kernel()
                            #this is the extra stuff which needs to be added to extend the basis to one of ker S too
                            #should add stuff from ker(S) which is in V but not in W. ie the stuff S sends straight to 0 from V / W
                            extra = V & S_ker
                            for new_vec in (extra & (extra & W).compliment()).basis:
                                V_bases.append([new_vec])

                            return V_bases

                    S_jcf_bases = get_S_jcf_bases(S, MatrixOver(algcls).Identity(n).col_span())
                    assert sum(len(basis) for basis in S_jcf_bases) == n
                    block_info[x] = S_jcf_bases
                return block_info #e.val -> jcf basis for that block

            def _jcf_ordered_basis(self, e_vals):                
                #return a basis which puts the matrix into JCF
                #with the blocks in the order given by e_vals
                assert len(set(e_vals)) == len(e_vals)
                assert len(e_vals) == len(set(self.eigen_val_list()))
                algcls = polycls.algcls

                e_gesp = self.general_eigen_col_spaces()
                basis = []
                for x in e_vals:
                    basis.extend(e_gesp[x].basis)
                B1 = MatrixOver(algcls).join_cols(basis)

                block_info = self._jcf_info()
                B2 = MatrixOver(algcls).join_diag([MatrixOver(algcls).join_cols(sum([list(basis) for basis in block_info[x]], [])) for x in e_vals])
                return B1 * B2

            @functools.cache
            def jcf_basis(self):                
                return self._jcf_ordered_basis(list(set(self.eigen_val_list())))

            @functools.cache
            def jcf(self):
                algcls = polycls.algcls
                T = self._lift_weird(algcls, self.polycls.as_root)
                B = self.jcf_basis()
                return B ** -1 * T * B

            def similar_basis(self, other):
                #find basis matrix P (if it exists) such that P ** -1 * self * P == other
                assert type(self) == type(other)
                assert (n := self.rows) == other.rows == self.cols == other.cols
                assert (e_vals := set(self.eigen_val_list())) == set(other.eigen_val_list())
                #find a basis so that self looks like other
                #find jcf basis for each such that the jcf is identical for each
                #algorithm always puts largest block first
                #just need to reorder eigen values if necessary
                e_vals = list(e_vals) #fix order

                self_B = self._jcf_ordered_basis(e_vals)
                other_B = other._jcf_ordered_basis(e_vals)

                return self_B * other_B ** -1

                
            
    return Matrix
    







@functools.cache
def SpanOver(ring):
    assert issubclass(ring, base.Ring)
    Matrix = MatrixOver(ring)

    def mat_to_row(rows, cols, mat):
        assert mat.rows == rows
        assert mat.cols == cols
        return Matrix(1, cols * rows, [[mat[i % rows, i // rows] for i in range(cols * rows)]])

    def row_to_mat(rows, cols, row_mat):
        assert row_mat.cols == rows * cols
        assert row_mat.rows == 1
        return Matrix(rows, cols, [[row_mat[0, r + c * rows] for c in range(cols)] for r in range(rows)])
    
    class Span():
        def __init__(self, rows, cols, matricies):
            assert type(rows) == int and rows >= 0
            assert type(cols) == int and rows >= 0
            for matrix in matricies:
                assert isinstance(matrix, Matrix)
                assert matrix.rows == rows
                assert matrix.cols == cols
                
            self.rows = rows
            self.cols = cols

            if len(matricies) == 0:
                self.basis = tuple([])
            else:
                _, _, pivs, H = Matrix.join_rows([mat_to_row(self.rows, self.cols, mat) for mat in matricies]).hermite_algorithm()
                self.basis = tuple(row_to_mat(self.rows, self.cols, H.row(i)) for i in range(len(pivs)))
        def __str__(self):
            if len(self.basis) == 0:
                return "{0}"
            else:
                rows = [""] * self.rows
                for idx, mat in enumerate(self.basis):
                    if idx != 0:
                        for r in range(self.rows):
                            if r == self.rows - 1:
                                rows[r] += " , "
                            else:
                                rows[r] += "   "
                    mat_str_rows = str(mat).split("\n")
                    for r in range(self.rows):
                        rows[r] += mat_str_rows[r]
                return "\n".join(rows)
        def __repr__(self):
            return "Span(" + ", ".join(repr(mat) for mat in self.basis) + ")"

        def __add__(self, other):
            if (cls := type(self)) == type(other):
                if (rows := self.rows) == other.rows and (cols := self.cols) == other.cols:
                    return cls(rows, cols, self.basis + other.basis)
            elif type(other) == Matrix:
                return self.as_offsetspan() + other
            return NotImplemented
        def __radd__(self, other):
            if type(other) == Matrix:
                return other + self.as_offsetspan()
            return NotImplemented
        def __and__(self, other):
            if (cls := type(self)) == type(other):
                if (rows := self.rows) == other.rows and (cols := self.cols) == other.cols:
                    metamatrix = Matrix.join_rows([mat_to_row(self.rows, self.cols, mat) for mat in self.basis] + [mat_to_row(other.rows, other.cols, mat) for mat in other.basis])
                    ker = metamatrix.row_kernel()

                    basis_rows = []
                    for coeffs in ker.basis:
                        basis_row = Matrix.zero(1, metamatrix.cols)                    
                        assert coeffs.cols == self.dimention() + other.dimention()
                        for i in range(0, self.dimention()):
                            basis_row += coeffs[0, i] * metamatrix.row(i)
                        basis_rows.append(basis_row)

                    return cls(rows, cols, [row_to_mat(self.rows, self.cols, row) for row in basis_rows])
            return NotImplemented

        def __mul__(self, other):
            if type(other) == Matrix:
                if other.rows == self.cols:
                    return type(self)(self.rows, other.cols, [mat * other for mat in self.basis])
                else:
                    raise Exception("Dimentions don't match for Span * Mat")
            return NotImplemented

        def __rmul__(self, other):
            if type(other) == Matrix:
                if other.cols == self.rows:
                    return type(self)(other.rows, self.cols, [other * mat for mat in self.basis])
                else:
                    raise Exception("Dimentions don't match for Mat * Span")
            return NotImplemented

        def dimention(self):
            return len(self.basis)
        def sample(self):
            if self.dimention == 0:
                raise Exception("No elements to sample from")
            else:
                return self.basis[0]

        def transpose(self):
            return type(self)(self.cols, self.rows, [mat.transpose() for mat in self.basis])

    return Span





















