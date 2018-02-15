# project influencemap @ANU

Goal: Constructing maps of intellectual influence using academic data.

We aim to make a service which allows users to easily search and visualise the
flow of academic influence through our influence flowers.

## methodology
To quantify academic influence, we define influence as a function of paper
citations. The scoring of influence is done with respect to entities
(author, institute, journal, or conference) and how entities cite other
entities. To visualise influence we use influence flowers. An influence
flower aims to show a dense representation of the influence in which an
entity (the center node, denoted as the ego) has with several other entities.

### calculating the influence one entity has on another entity

#### removing self-citations

We define a self-citation between papers and a cited paper as a relation
dependent on the ego. A paper citation is a self-citation if both papers
have the ego as an author.

#### Why not remove all coauthor papers instead?
 
When removing all coauthor papers (all scores from papers with a coauthor of
the referencing paper authors) we found the 'cut down' to be too extreme. This
would greatly effect the produced flower, leaving one with little to no
information.

#### weighting the citations



#### Normalisation

Influence on an entity is calculated as the sum of the per author weight for each of the citations to a paper written by that entity, as shown below.

![calculation of a's influence on b](https://github.com/csmetrics/influencemap/blob/master/assets/influence_calulation.png)

For example, consider the following four paper database.

| Name         | Paper            | no. authors | cites papers                     |
|--------------|------------------|-------------|----------------------------------|
| John Smith   | Algorithms       | 2           | [Linear Algebra]                 |
| John Smith   | Machine Learning | 3           | [Linear Algebra, Computation]    |
| Maria Garcia | Linear Algebra   | 2           | None                             |
| Maria Garcia | Computation      | 4           | [Algorithms]                     |

In this case John's influence on Maria is 0.5 (John's paper Algorithm's has a weight of 0.5 and was cited once by Maria). 

On the other hand Maria's influence on John is 1.25 (Linear Algebra has a weight of 0.5 and it was cited twice by John, Computation has a weight of 0.25 and was cited once by John).

#### page-rank style weighting of papers

[TODO] generate sample graphics using different weighting schemes

### one database containing all useful tables

[TBD]

### how data is cached

[TBD]

### visualising the influence
To visualise the influence that one entity has on others, the influence scores are calculated as described above for the entity and each other entity that cites it. The scores of the most influential entities are normalised and used as weights for the graph's edges to show their relative influence. Similarly, visualising how one is influenced involves finding the scores for each entity that has influenced (been cited by) them and plotting the normalised scores as weights on a weighted graph.
