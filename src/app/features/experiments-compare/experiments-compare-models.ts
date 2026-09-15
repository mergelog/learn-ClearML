import {ExperimentDetailBase, TreeNode} from '@common/experiments-compare/shared/experiments-compare-details.model';
import {TreeNodeJsonData} from '@common/experiments-compare/jsonToDiffConvertor';


export type ExperimentCompareTreeSection = TreeNode<{ data?: Array<TreeNode<TreeNodeJsonData>>; key: string}>;

export interface ExperimentCompareTree {
  model?: ExperimentCompareTreeSection;
  execution?: ExperimentCompareTreeSection;
}

export type IExperimentDetail = ExperimentDetailBase;
