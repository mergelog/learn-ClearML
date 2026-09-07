import type {IExecutionForm} from '~/features/experiments/shared/experiment-execution.model';
import type {IOption} from '@common/shared/ui-components/inputs/select-autocomplete-with-chips/select-autocomplete-with-chips.component';

const defaultRequirement = 'pip';

const requirementLabels: Record<string, string> = {
  pip: 'PIP',
  orgPip: 'Original PIP',
  conda: 'Conda',
  orgConda: 'Original Conda'
};

export interface ExecutionRequirementsState {
  options: IOption[];
  selected: string;
  editable: boolean;
  resetTooltip: string;
}

export function createExecutionRequirementsState(
  formData: IExecutionForm | undefined,
  selectedRequirement: string
): ExecutionRequirementsState {
  if (!formData) {
    return {
      options: [],
      selected: defaultRequirement,
      editable: true,
      resetTooltip: ''
    };
  }

  const requirements = formData.requirements ?? {};
  const options = Object.keys(requirementLabels)
    .filter(key => Object.hasOwn(requirements, key))
    .map(key => ({
      value: key,
      label: requirementLabels[key]
    }));
  const selected = Object.hasOwn(requirements, selectedRequirement) ?
    selectedRequirement :
    defaultRequirement;
  const originalRequirements = [
    requirements.orgPip ? 'original-pip' : '',
    requirements.orgConda ? 'original-conda' : ''
  ].filter(Boolean).join(' / ');

  return {
    options,
    selected,
    editable: selected === defaultRequirement,
    resetTooltip: `Set packages to originally recorded values (${originalRequirements})`
  };
}
