*KEYWORD
*TITLE
U-channel draw, DC04 t=0.8mm, BHF=10 kN
$ units: mm / ms / kg / kN / GPa
$ blank 350 x 35 x 0.8 mm, element 2 mm
$ punch 50 mm wide, nose R5, die shoulder R5
$ draw depth 70 mm, blankholder force 10 kN
$ writes dynain at termination for the implicit springback run
*CONTROL_TERMINATION
$#  endtim    endcyc     dtmin    endeng    endmas     nosol
      17.0         0       0.0       0.0       0.0         0
*CONTROL_TIMESTEP
$#  dtinit    tssfac      isdo    tslimt     dt2ms      lctm     erode     ms1st
       0.0       0.9         0       0.0   -0.0003         0         1         0
*CONTROL_ENERGY
$#    hgen      rwen    slnten     rylen     irgen
         2         2         2         2         2
*CONTROL_HOURGLASS
$#     ihq        qh
         4      0.05
*CONTROL_SHELL
$#  wrpang     esort     irnxx    istupd    theory       bwc     miter      proj
      20.0         1        -1         1         2         2         1         0
*CONTROL_CONTACT
$#  slsfac    rwpnal    islchk    shlthk    penopt    thkchg     orien    enmass
       0.1       0.0         2         1         4         1         1         0
$#  usrstr    usrfrc     nsbcs    interm     xpene     ssthk      ecdt   tiedprj
         0         0         0         0       4.0         0         0         0
*CONTROL_ACCURACY
$#     osu       inn    pidosu      iacc
         1         4         0         1
*DATABASE_GLSTAT
$#      dt    binary      lcur     ioopt
      0.05         3         0         1
*DATABASE_MATSUM
$#      dt    binary      lcur     ioopt
      0.05         3         0         1
*DATABASE_RCFORC
$#      dt    binary      lcur     ioopt
      0.05         3         0         1
*DATABASE_SLEOUT
$#      dt    binary      lcur     ioopt
      0.05         3         0         1
*DATABASE_NODOUT
$#      dt    binary      lcur     ioopt
      0.05         3         0         1
*DATABASE_ELOUT
$#      dt    binary      lcur     ioopt
      0.05         3         0         1
*DATABASE_SECFORC
$#      dt    binary      lcur     ioopt
      0.05         3         0         1
*DATABASE_SPCFORC
$#      dt    binary      lcur     ioopt
      0.05         3         0         1
*DATABASE_RWFORC
$#      dt    binary      lcur     ioopt
      0.05         3         0         1
*DATABASE_BNDOUT
$#      dt    binary      lcur     ioopt
      0.05         3         0         1
*DATABASE_BINARY_D3PLOT
$#      dt      lcdt      beam     npltc    psetid
       1.0         0         0         0         0
*DATABASE_EXTENT_BINARY
$#   neiph     neips    maxint    strflg    sigflg    epsflg    rltflg    engflg
         0         0        -3         1         1         1         1         1
$#  cmpflg    ieverp    beamip     dcomp      shge     stssz    n3thdt   ialemat
         0         1         0         1         2         3         2         1
*PART
blank DC04
$#     pid     secid       mid     eosid      hgid      grav    adpopt      tmid
         1         1         1         0         1         0         0         0
*PART
die
$#     pid     secid       mid     eosid      hgid      grav    adpopt      tmid
         2         2         2         0         0         0         0         0
*PART
punch
$#     pid     secid       mid     eosid      hgid      grav    adpopt      tmid
         3         2         3         0         0         0         0         0
*PART
blankholder
$#     pid     secid       mid     eosid      hgid      grav    adpopt      tmid
         4         2         4         0         0         0         0         0
*SECTION_SHELL_TITLE
blank, type 16, 7 integration points through thickness
$#   secid    elform      shrf       nip     propt   qr/irid     icomp     setyp
         1        16    0.8333         7       1.0       0.0         0         1
$#      t1        t2        t3        t4
       0.8       0.8       0.8       0.8
*SECTION_SHELL_TITLE
rigid tool surfaces
$#   secid    elform      shrf       nip     propt   qr/irid     icomp     setyp
         2         2    0.8333         2       1.0       0.0         0         1
$#      t1        t2        t3        t4
       1.0       1.0       1.0       1.0
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
*MAT_RIGID_TITLE
die
$#     mid        ro         e        pr         n    couple         m     alias
         2   7.85e-6     210.0       0.3       0.0       0.0       0.0       0.0
$#     cmo      con1      con2
       1.0         7         7
$#  lco/a1        a2        a3        v1        v2        v3
       0.0       0.0       0.0       0.0       0.0       0.0
*MAT_RIGID_TITLE
punch
$#     mid        ro         e        pr         n    couple         m     alias
         3   7.85e-6     210.0       0.3       0.0       0.0       0.0       0.0
$#     cmo      con1      con2
       1.0         4         7
$#  lco/a1        a2        a3        v1        v2        v3
       0.0       0.0       0.0       0.0       0.0       0.0
*MAT_RIGID_TITLE
blankholder
$#     mid        ro         e        pr         n    couple         m     alias
         4   7.85e-6     210.0       0.3       0.0       0.0       0.0       0.0
$#     cmo      con1      con2
       1.0         4         7
$#  lco/a1        a2        a3        v1        v2        v3
       0.0       0.0       0.0       0.0       0.0       0.0
*DEFINE_CURVE_TITLE
punch velocity [mm/ms]
$#    lcid      sidr       sfa       sfo      offa      offo    dattyp     lcint
       200         0       1.0       1.0       0.0       0.0         0         0
                 0.0                 0.0
                 1.0                 5.0
                17.0                 5.0
*DEFINE_CURVE_TITLE
blankholder force [kN]
$#    lcid      sidr       sfa       sfo      offa      offo    dattyp     lcint
       201         0       1.0       1.0       0.0       0.0         0         0
                 0.0                 0.0
                 0.5                10.0
                17.0                10.0
*BOUNDARY_PRESCRIBED_MOTION_RIGID
$#     pid       dof       vad      lcid        sf       vid     death     birth
         3         3         0       200      -1.0         0    1.0e20       0.0
*LOAD_RIGID_BODY
$#     pid       dof      lcid        sf       cid        m1        m2        m3
         4         3       201      -1.0         0         0         0         0
*SET_PART_LIST
        10       0.0       0.0       0.0       0.0
         1
*SET_PART_LIST
        11       0.0       0.0       0.0       0.0
         2
*SET_PART_LIST
        12       0.0       0.0       0.0       0.0
         3
*SET_PART_LIST
        13       0.0       0.0       0.0       0.0
         4
*CONTACT_FORMING_ONE_WAY_SURFACE_TO_SURFACE_ID
         1blank to die
$#    ssid      msid     sstyp     mstyp    sboxid    mboxid       spr       mpr
        10        11         2         2         0         0         1         1
$#      fs        fd        dc        vc       vdc    penchk        bt        dt
     0.125     0.125       0.0       0.0      10.0         0       0.0    1.0e20
$#     sfs       sfm       sst       mst      sfst      sfmt       fsf       vsf
       1.0       1.0       0.0       0.0       1.0       1.0       1.0       1.0
$#    soft    sofscl    lcidab    maxpar     sbopt     depth     bsort    frcfrq
         1       0.1         0     1.025       2.0         5         0         1
*CONTACT_FORMING_ONE_WAY_SURFACE_TO_SURFACE_ID
         2blank to punch
$#    ssid      msid     sstyp     mstyp    sboxid    mboxid       spr       mpr
        10        12         2         2         0         0         1         1
$#      fs        fd        dc        vc       vdc    penchk        bt        dt
     0.125     0.125       0.0       0.0      10.0         0       0.0    1.0e20
$#     sfs       sfm       sst       mst      sfst      sfmt       fsf       vsf
       1.0       1.0       0.0       0.0       1.0       1.0       1.0       1.0
$#    soft    sofscl    lcidab    maxpar     sbopt     depth     bsort    frcfrq
         1       0.1         0     1.025       2.0         5         0         1
*CONTACT_FORMING_ONE_WAY_SURFACE_TO_SURFACE_ID
         3blank to blankholder
$#    ssid      msid     sstyp     mstyp    sboxid    mboxid       spr       mpr
        10        13         2         2         0         0         1         1
$#      fs        fd        dc        vc       vdc    penchk        bt        dt
     0.125     0.125       0.0       0.0      10.0         0       0.0    1.0e20
$#     sfs       sfm       sst       mst      sfst      sfmt       fsf       vsf
       1.0       1.0       0.0       0.0       1.0       1.0       1.0       1.0
$#    soft    sofscl    lcidab    maxpar     sbopt     depth     bsort    frcfrq
         1       0.1         0     1.025       2.0         5         0         1
*INCLUDE
mesh.k
*INTERFACE_SPRINGBACK_LSDYNA
$#    psid      nshv     ftype    ftensr    nthhsv     rflag   intstrn      optc
        10         0         0         0         0         0         0
*END
