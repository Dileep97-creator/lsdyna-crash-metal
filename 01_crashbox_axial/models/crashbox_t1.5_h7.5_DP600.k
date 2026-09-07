*KEYWORD
*TITLE
crash box DP600 t=1.5mm h=7.5mm 500kg @ 15m/s
$ units: mm / ms / kg / kN / GPa   (energy in kN-mm = J)
$ element size 7.5 mm, wall thickness 1.5 mm, material DP600
$ acceptance: hourglass < 5% and added mass < 5% of the model mass
*CONTROL_TERMINATION
$#  endtim    endcyc     dtmin    endeng    endmas     nosol
      25.0         0       0.0       0.0       0.0         0
*CONTROL_TIMESTEP
$#  dtinit    tssfac      isdo    tslimt     dt2ms      lctm     erode     ms1st
       0.0       0.9         0       0.0   -0.0008         0         1         0
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
       0.5         0         0         0         0
*DATABASE_EXTENT_BINARY
$#   neiph     neips    maxint    strflg    sigflg    epsflg    rltflg    engflg
         0         0        -3         1         1         1         1         1
$#  cmpflg    ieverp    beamip     dcomp      shge     stssz    n3thdt   ialemat
         0         1         0         1         2         3         2         1
*DATABASE_HISTORY_NODE_SET
        11
*PART
crash box DP600 t=1.5
$#     pid     secid       mid     eosid      hgid      grav    adpopt      tmid
         1         1         1         0         1         0         0         0
*PART
rigid impactor
$#     pid     secid       mid     eosid      hgid      grav    adpopt      tmid
         2         2         2         0         0         0         0         0
*SECTION_SHELL_TITLE
tube, type 16 fully integrated
$#   secid    elform      shrf       nip     propt   qr/irid     icomp     setyp
         1        16    0.8333         5       1.0       0.0         0         1
$#      t1        t2        t3        t4      nloc     marea      idof    edgset
       1.5       1.5       1.5       1.5       0.0       0.0       0.0         0
*SECTION_SHELL_TITLE
impactor plate
$#   secid    elform      shrf       nip     propt   qr/irid     icomp     setyp
         2         2    0.8333         2       1.0       0.0         0         1
$#      t1        t2        t3        t4
       5.0       5.0       5.0       5.0
*HOURGLASS
$#    hgid       ihq        qm       ibq        q1        q2    qb/vdc        qw
         1         4      0.05         0       1.5      0.06       0.0       0.0
*DEFINE_CURVE_TITLE
DP600 effective stress vs plastic strain [GPa]
$#    lcid      sidr       sfa       sfo      offa      offo    dattyp     lcint
       100         0       1.0       1.0       0.0       0.0         0         0
                 0.0         0.405143105
       0.00474341649         0.466653921
        0.0134164079         0.525421777
        0.0246475151          0.57147184
        0.0379473319         0.609149876
        0.0530330086         0.641160961
        0.0697137002          0.66910606
        0.0878493028         0.693990601
         0.107331263         0.716484008
         0.128072245         0.737054041
                0.15         0.756040581
          0.17305346         0.773698586
         0.197180121         0.790224414
         0.222334208         0.805772664
         0.248475351         0.820467352
         0.275567596         0.834409572
         0.303578655         0.847682883
         0.332479323         0.860357196
         0.362243012         0.872491633
         0.392845389          0.88413667
         0.424264069         0.895335768
         0.456478368         0.906126636
           0.4894691         0.916542219
         0.523218406          0.92661148
         0.557709602         0.936360026
         0.592927061         0.945810619
         0.628856104         0.954983587
         0.665482907         0.963897166
         0.702794422          0.97256778
         0.740778307         0.981010282
         0.779422863         0.989238148
         0.818716984         0.997263647
         0.858650103          1.00509798
         0.899212155          1.01275141
         0.940393535          1.02023336
         0.982185064          1.02755251
          1.02457796          1.03471685
          1.06756382           1.0417338
          1.11113456          1.04861022
          1.15528243          1.05535249
                 1.2          1.06196653
*MAT_PIECEWISE_LINEAR_PLASTICITY_TITLE
DP600 (representative flow curve)
$#     mid        ro         e        pr      sigy      etan      fail      tdel
         1   7.85e-6     210.0       0.3      0.36       0.0       0.0       0.0
$#       c         p      lcss      lcsr        vp
      10.0       5.0       100         0       1.0
$#    eps1      eps2      eps3      eps4      eps5      eps6      eps7      eps8
       0.0       0.0       0.0       0.0       0.0       0.0       0.0       0.0
$#     es1       es2       es3       es4       es5       es6       es7       es8
       0.0       0.0       0.0       0.0       0.0       0.0       0.0       0.0
*MAT_RIGID_TITLE
impactor
$#     mid        ro         e        pr         n    couple         m     alias
         2 0.0069444     210.0       0.3       0.0       0.0       0.0       0.0
$#     cmo      con1      con2
       1.0         4         7
$#  lco/a1        a2        a3        v1        v2        v3
       0.0       0.0       0.0       0.0       0.0       0.0
*BOUNDARY_SPC_SET
$#    nsid       cid      dofx      dofy      dofz     dofrx     dofry     dofrz
        10         0         1         1         1         1         1         1
*INITIAL_VELOCITY_GENERATION
$#      id      styp     omega        vx        vy        vz     ivatn      icid
         2         2       0.0       0.0       0.0     -15.0         0         0
$#      xc        yc        zc        nx        ny        nz     phase    irigid
       0.0       0.0       0.0       0.0       0.0       0.0         0         0
*SET_PART_LIST
        20       0.0       0.0       0.0       0.0
         1
*SET_PART_LIST
        21       0.0       0.0       0.0       0.0
         2
*CONTACT_AUTOMATIC_SINGLE_SURFACE_ID
         1self contact of the folding tube
$#    ssid      msid     sstyp     mstyp    sboxid    mboxid       spr       mpr
        20         0         2         0         0         0         1         1
$#      fs        fd        dc        vc       vdc    penchk        bt        dt
       0.2      0.15       0.0       0.0      20.0         0       0.0    1.0e20
$#     sfs       sfm       sst       mst      sfst      sfmt       fsf       vsf
       1.0       1.0       0.0       0.0       1.0       1.0       1.0       1.0
$#    soft    sofscl    lcidab    maxpar     sbopt     depth     bsort    frcfrq
         1       0.1         0     1.025       2.0         2         0         1
*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID
         2impactor to tube
$#    ssid      msid     sstyp     mstyp    sboxid    mboxid       spr       mpr
        20        21         2         2         0         0         1         1
$#      fs        fd        dc        vc       vdc    penchk        bt        dt
      0.15       0.1       0.0       0.0      20.0         0       0.0    1.0e20
$#     sfs       sfm       sst       mst      sfst      sfmt       fsf       vsf
       1.0       1.0       0.0       0.0       1.0       1.0       1.0       1.0
$#    soft    sofscl    lcidab    maxpar     sbopt     depth     bsort    frcfrq
         1       0.1         0     1.025       2.0         2         0         1
*INCLUDE
mesh_h7.5.k
*END
