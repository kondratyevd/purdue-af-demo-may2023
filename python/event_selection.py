# based on https://github.com/piperov/Purdue_AF_Demo by Stefan Piperov, Amandeep Kaur, and Dmitry Kondratyev

import pandas as pd
import uproot
import awkward as ak
import vector
vector.register_awkward()

def load_events(file, max_events = None, use_dask_df=False):
        tree = uproot.open(file)["Events"]
        branches = [
            "nMuon", "Muon_pt", "Muon_eta", "Muon_charge",
            "Muon_isGlobal", "Muon_phi", "Muon_mass", "MET_pt"
        ]

        tree = uproot.open(file)["Events"].arrays(
            filter_name=branches,
            entry_start=0, entry_stop=max_events
        )

        all_muons = ak.Array(
            ak.zip(
                {
                    "nmu": tree["nMuon"], 
                    "mu_pt": tree["Muon_pt"],
                    "mu_eta": tree["Muon_eta"],
                    "mu_charge": tree["Muon_charge"],
                    "mu_id": tree["Muon_isGlobal"],
                    "mu_phi": tree["Muon_phi"],
                    "mu_mass": tree["Muon_mass"],
                    "met": tree["MET_pt"]
                }
            )
        )
        muons_mask = (all_muons.mu_id==1) & (all_muons.mu_pt > 20) & (abs(all_muons.mu_eta)<2.4)
        good_muons = all_muons[muons_mask]
        good_muons = good_muons[(ak.sum(muons_mask,axis=-1)==2)]
        opp_sign = good_muons.mu_charge[:,0]!=good_muons.mu_charge[:,1]
        good_muons = good_muons[opp_sign]
        
        mu_p4 = ak.Array(
            ak.zip(
                {
                    "pt": good_muons.mu_pt,
                    "eta": good_muons.mu_eta,
                    "phi": good_muons.mu_phi,
                    "mass": good_muons.mu_mass
                }
            ),
            with_name = "Momentum4D"
        )


        ## Converting awkward arrays to panda dataframes
        df_mu1 = ak.to_pandas(mu_p4[:,0])
        df_mu1 = df_mu1.add_prefix('mu1_')

        df_mu2 = ak.to_pandas(mu_p4[:,1])
        df_mu2 = df_mu2.add_prefix('mu2_')

        df = pd.concat([df_mu1, df_mu2], axis=1)
        
        dimuons = mu_p4[:,0] + mu_p4[:,1]
        df["dimuon_mass"] = dimuons.M

        df["met"] = pd.DataFrame(good_muons.met[:,0])

        df = df.astype(float)
    
        if use_dask_df:
            return dd.from_pandas(df, npartitions=1)
        else:
            return df

