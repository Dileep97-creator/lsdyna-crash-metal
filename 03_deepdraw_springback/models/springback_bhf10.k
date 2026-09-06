*KEYWORD
*TITLE
U-channel springback, DC04 t=0.8mm, BHF=10 kN
$ implicit static release of the drawn blank
$ run forming_bhf10.k first, then copy its dynain next to this deck
$ rigid body modes are removed by a three-node minimal constraint,
$ not by clamping an edge - clamping would suppress the sidewall
$ curl this model exists to measure
*CONTROL_TERMINATION
$#  endtim    endcyc     dtmin    endeng    endmas     nosol
       1.0         0       0.0       0.0       0.0         0
*CONTROL_IMPLICIT_GENERAL
$#  imflag       dt0    imform      nsbs      igso     cnstn      form    zero_v
         1       0.1         2         1         0         0         0         0
*CONTROL_IMPLICIT_AUTO
$#   iauto    iteopt    itewin     dtmin     dtmax     dtexp     kfail    kcycle
         1        11         5     0.001       0.1       0.0         0         0
*CONTROL_IMPLICIT_SOLUTION
$#  nsolvr    ilimit    maxref     dctol     ectol     rctol     lstol    abstol
        12        11        55     0.001      0.01    1.0e10       0.9   1.0e-10
$#   dnorm    diverg     istif   nlprint    nlnorm   d3itctl     cpchk
         2         1         1         2         4         0         0
$#  arcctl    arcdir    arclen    arcmth    arcdmp    arcpsi    arcalf    arctim
         0         0       0.0         1         2       0.0       0.0       0.0
*CONTROL_IMPLICIT_SOLVER
$#  lsolvr    lprint     negev     order      drcm    drcprm   autospc   aspctol
         2         0         2         0         4       0.0         1       0.0
*CONTROL_SHELL
$#  wrpang     esort     irnxx    istupd    theory       bwc     miter      proj
      20.0         1        -1         1         2         2         1         0
*DATABASE_BINARY_D3PLOT
$#      dt      lcdt      beam     npltc    psetid
       0.1         0         0         0         0
*DATABASE_GLSTAT
$#      dt    binary
      0.05         3
*DATABASE_NODOUT
$#      dt    binary
      0.05         3
*INCLUDE
dynain
*PART
blank DC04
$#     pid     secid       mid     eosid      hgid      grav    adpopt      tmid
         1         1         1         0         1         0         0         0
*SECTION_SHELL_TITLE
blank, type 16, 7 integration points through thickness
$#   secid    elform      shrf       nip     propt   qr/irid     icomp     setyp
         1        16    0.8333         7       1.0       0.0         0         1
$#      t1        t2        t3        t4
       0.8       0.8       0.8       0.8
*HOURGLASS
$#    hgid       ihq        qm       ibq        q1        q2    qb/vdc        qw
         1         4      0.05         0       1.5      0.06       0.0       0.0
*DEFINE_CURVE_TITLE
DC04 flow curve [GPa]
$#    lcid      sidr       sfa       sfo      offa      offo    dattyp     lcint
       100         0       1.0       1.0       0.0       0.0         0         0
                 0.0                0.18
       0.00474341649         0.190690297
        0.0134164079         0.216556446
        0.0246475151         0.239526728
        0.0379473319         0.259655646
        0.0530330086         0.277527226
        0.0697137002         0.293627443
        0.0878493028         0.308314338
         0.107331263         0.321850227
         0.128072245         0.334430653
                0.15         0.346204565
          0.17305346         0.357287817
         0.197180121         0.367772257
         0.222334208         0.377731934
         0.248475351         0.387227454
         0.275567596          0.39630907
         0.303578655         0.405018946
         0.332479323         0.413392825
         0.362243012         0.421461293
         0.392845389         0.429250738
         0.424264069         0.436784102
         0.456478368         0.444081465
           0.4894691         0.451160512
         0.523218406         0.458036907
         0.557709602         0.464724597
         0.592927061         0.471236057
         0.628856104         0.477582499
         0.665482907         0.483774037
         0.702794422          0.48981983
         0.740778307         0.495728203
         0.779422863         0.501506747
         0.818716984         0.507162402
         0.858650103         0.512701536
         0.899212155         0.518130005
         0.940393535         0.523453208
         0.982185064         0.528676135
          1.02457796         0.533803408
          1.06756382         0.538839319
          1.11113456         0.543787857
          1.15528243         0.548652743
                 1.2         0.553437448
*MAT_3-PARAMETER_BARLAT_TITLE
DC04 Barlat89 (representative)
$#     mid        ro         e        pr        hr        p1        p2      iter
         1   7.85e-6     210.0       0.3       3.0       0.0       0.0       1.0
$#       m       r00       r45       r90      lcid        e0       spi        p3
       6.0       1.8      1.45       2.1       100       0.0       0.0       0.0
$#    aopt         c         p     vlcid                                        
       0.0       0.0       0.0         0
$#      xp        yp        zp        a1        a2        a3
       0.0       0.0       0.0       0.0       0.0       0.0
$#      v1        v2        v3        d1        d2        d3      beta
       0.0       0.0       0.0       0.0       0.0       0.0       0.0
*BOUNDARY_SPC_NODE
$#     nid       cid      dofx      dofy      dofz     dofrx     dofry     dofrz
      1663         0         1         1         1         0         0         0
$#     nid       cid      dofx      dofy      dofz     dofrx     dofry     dofrz
      1758         0         0         1         1         0         0         0
$#     nid       cid      dofx      dofy      dofz     dofrx     dofry     dofrz
      1654         0         0         0         1         0         0         0
*INTERFACE_SPRINGBACK_LSDYNA
$#    psid      nshv     ftype    ftensr    nthhsv     rflag   intstrn      optc
        10         0         0         0         0         0         0
*SET_PART_LIST
        10       0.0       0.0       0.0       0.0
         1
*END
