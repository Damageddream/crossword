import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        for key in self.domains:
            domainCopy = self.domains[key].copy()
            for word in domainCopy:
                if len(word) != key.length:
                    self.domains[key].remove(word)


    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        overlap = self.crossword.overlaps[x,y]
        if not overlap:
            return False
        revisone_made = False 
        x_domains = self.domains[x].copy()
        for val_x in x_domains:
            count = 0
            for val_y in self.domains[y]:
                if val_y[overlap[1]] != val_x[overlap[0]]:
                    count += 1
                if count == len(self.domains[y]):
                    self.domains[x].remove(val_x)
                    revisone_made = True
        return revisone_made



    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        if not arcs:
            arcs = []
            for variable in self.crossword.variables:
                neighbors = self.crossword.neighbors(variable)
                for neighbor in neighbors:   
                    if (variable, neighbor) not in arcs:
                        arcs.append((variable,neighbor))
        while len(arcs) != 0:
            (x,y) = arcs.pop(0)
            if self.revise(x,y):
                if(len(self.domains[x]) == 0):
                    return False
                x_neighbors = self.crossword.neighbors(x)
                x_neighbors.remove(y)
                for z in x_neighbors:
                    arcs.append((z,x))
        return True


    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for key in assignment:
            if key not in assignment:
                return False
            if not assignment[key]:
                return False
        if len(assignment) != len(self.crossword.variables):
             return False
        return True
    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        word = None
        for key in assignment:
            if key.length != len(assignment[key]):
                return False           
            if assignment[key] != word:
                word = assignment[key]
            elif assignment[key] == word:
                return False

            neighbors = self.crossword.neighbors(key)
            for neighbor in neighbors:
                overlap = self.crossword.overlaps[key,neighbor]
                if overlap:
                    if assignment[key][overlap[0]] != self.domains[neighbor].copy().pop()[overlap[1]]:
                        return False
            
        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        assign_values = dict()

        neighbors = self.crossword.neighbors(var)
        for value in self.domains[var]:
            assign_values[value] = 0
            for neighbor in neighbors:
                if neighbor in assignment:
                    continue                
                overlap = self.crossword.overlaps[var, neighbor]
                for neighbor_value in self.domains[neighbor]:
                    if value[overlap[0]] == neighbor_value[overlap[1]]:
                        assign_values[value] += 1
        sorted_values = sorted(assign_values, key=assign_values.get)
        return list(sorted_values)

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        # selected_var = None
        # for var in self.crossword.variables:
        #     if var in assignment:
        #         continue
        #     if not selected_var:
        #         selected_var = var
        #     if len(self.domains[selected_var]) > len(self.domains[var]):
        #         selected_var = var
        #     if len(self.domains[selected_var]) == len(self.domains[var]):
        #         selected_var_degree = len(self.crossword.neighbors(selected_var))
        #         var_degree = len(self.crossword.neighbors(var))
        #         if var_degree > selected_var_degree:
        #             selected_var = var
        # return selected_var

        for var in self.crossword.variables:
            if var not in assignment:
                return var


    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if self.assignment_complete(assignment):
            return assignment
        var = self.select_unassigned_variable(assignment)
        for value in self.order_domain_values(var, assignment):  
            temp_dic = assignment.copy()
            temp_dic[var] = value
            if self.consistent(temp_dic):
                assignment[var] = value
                result = self.backtrack(assignment)
                if result:
                    return result
                del assignment[var]
        return None



def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
